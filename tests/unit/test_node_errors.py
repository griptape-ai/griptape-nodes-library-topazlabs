"""Tests for the errors the Topaz Labs nodes raise.

The nodes run for real. Only `requests.adapters.HTTPAdapter.send` and the secret lookup are replaced, so
`requests` builds the exceptions itself. None of the nodes has a Failed output, so there is no wired case.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import urlparse

import base_topaz_node
import base_topaz_video_node
import pytest
import requests
from griptape.artifacts import BlobArtifact, ImageArtifact
from griptape_nodes.exe_types.core_types import NodeError
from topaz_client import TopazClient

LIBRARY_DIR = Path(__file__).resolve().parents[2] / "topazlabs"
KEY_LINK = "#settings-secrets?filter=TOPAZ_LABS_API_KEY"
IMAGE_NODES = [
    ("topaz_denoise_node", "TopazDenoiseNode"),
    ("topaz_enhance_node", "TopazEnhanceNode"),
    ("topaz_creative_enhance_node", "TopazCreativeEnhanceNode"),
]
VIDEO_NODES = [
    ("topaz_video_upscale_node", "TopazVideoUpscaleNode"),
    ("topaz_video_denoise_node", "TopazVideoDenoiseNode"),
    ("topaz_frame_interpolation_node", "TopazFrameInterpolationNode"),
]
NODES = IMAGE_NODES + VIDEO_NODES

# What the live API answered to a made-up key. The image API and the video API differ.
IMAGE_401 = {"message": "Invalid authentication token"}
VIDEO_401 = {"message": "Unauthorized", "errorCode": "UNAUTHORIZED"}
IMAGE = ImageArtifact(b"x" * 200, format="png", width=1, height=1)
VIDEO = BlobArtifact(b"x" * 2000)
STORAGE = "storage.example.com"


def _node(module_name: str, class_name: str) -> Any:
    return getattr(importlib.import_module(module_name), class_name)(name="Some Node")


def _force(node: Any, name: str, value: Any) -> None:
    """Set a value the Slider trait would refuse, as a wired upstream value can arrive unchecked."""
    node.parameter_values[name] = value


def _is_video(module_name: str) -> bool:
    return module_name in {name for name, _ in VIDEO_NODES}


def _with_input(node: Any, module_name: str) -> Any:
    video = _is_video(module_name)
    node.set_parameter_value("video_input" if video else "image_input", VIDEO if video else IMAGE)
    return node


@pytest.fixture(autouse=True)
def secret(monkeypatch: pytest.MonkeyPatch) -> dict[str, str | None]:
    """The API key the nodes see. Set `secret["key"] = None` for a missing key."""
    holder: dict[str, str | None] = {"key": "test-key"}
    engine = MagicMock()
    engine.SecretsManager.return_value.get_secret.side_effect = lambda _name: holder["key"]
    for module in (base_topaz_node, base_topaz_video_node):
        monkeypatch.setattr(module, "GriptapeNodes", engine)

    async def no_wait(_seconds: float) -> None:
        await real_sleep(0.01)

    real_sleep = asyncio.sleep
    monkeypatch.setattr(base_topaz_video_node.asyncio, "sleep", no_wait)
    monkeypatch.setattr("time.sleep", lambda _s: None)
    return holder


def _network(monkeypatch: pytest.MonkeyPatch, route: Callable[[requests.PreparedRequest], Any]) -> None:
    """Answer every request with `route(request)`: (status, body[, headers]) or an exception to raise."""

    def send(self: Any, request: requests.PreparedRequest, **_kwargs: Any) -> requests.Response:
        answer = route(request)
        if isinstance(answer, Exception):
            raise answer
        status, body, *rest = answer
        response = requests.Response()
        response.status_code = status
        response.url = request.url or ""
        response.request = request
        response.encoding = "utf-8"
        response.headers.update(rest[0] if rest else {})
        response._content = (body if isinstance(body, str) else json.dumps(body) if body is not None else "").encode()
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)


def _route(video: bool, **overrides: Any) -> Callable[[requests.PreparedRequest], Any]:
    """Canned answers for a whole job. `overrides` replaces the answer for one step."""
    steps: dict[str, Any] = {
        "file": (200, "bytes"),
        "upload": (200, "", {"ETag": '"abc"'}),
        "create": (200, {"requestId": "r1"}),
        "accept": (200, {"urls": [f"https://{STORAGE}/up"]}),
        "complete": (200, {}),
        "status": (200, {"status": "complete", "download": {"url": f"https://{STORAGE}/down"}})
        if video
        else (200, {"status": "Completed"}),
        "start": (200, {"process_id": "p1"}),
        "download": (200, {"download_url": f"https://{STORAGE}/down"}),
    } | overrides

    def route(request: requests.PreparedRequest) -> Any:
        parts = urlparse(request.url or "")
        if parts.netloc == STORAGE:
            return steps["upload" if request.method == "PUT" else "file"]
        if not video:
            return steps["start" if request.method == "POST" else "status" if "/status/" in parts.path else "download"]
        for suffix, step in (("/accept", "accept"), ("/complete-upload", "complete"), ("/status", "status")):
            if parts.path.endswith(suffix):
                return steps[step]
        return steps["create"]

    return route


def _run(node: Any) -> NodeError:
    with pytest.raises(NodeError) as raised:
        node._process_sync()
    return raised.value


def _fail(
    monkeypatch: pytest.MonkeyPatch, module_name: str, class_name: str, always: Any = None, **steps: Any
) -> NodeError:
    """Run a node with an input connected. `always` answers every request, else `steps` override one step."""
    node = _with_input(_node(module_name, class_name), module_name)
    _network(monkeypatch, (lambda _r: always) if always is not None else _route(_is_video(module_name), **steps))
    return _run(node)


@pytest.mark.parametrize(("module_name", "class_name"), NODES)
def test_a_node_file_loads_the_way_the_engine_loads_it(
    module_name: str, class_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The engine loads each file on its own with the library folder on sys.path and no parent package."""
    monkeypatch.syspath_prepend(str(LIBRARY_DIR))
    monkeypatch.setitem(sys.modules, "topazlabs", None)
    spec = importlib.util.spec_from_file_location(f"engine_loaded_{module_name}", LIBRARY_DIR / f"{module_name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, class_name)


@pytest.mark.parametrize(("module_name", "class_name"), NODES)
def test_a_missing_key_is_the_only_problem_and_nothing_is_checked_at_flow_start(
    module_name: str, class_name: str, secret: dict[str, str | None]
) -> None:
    secret["key"] = None
    node = _node(module_name, class_name)
    for name, value in (("strength", 5.0), ("sharpen", 5.0), ("processing_timeout", 1)):
        if node.get_parameter_by_name(name):
            _force(node, name, value)

    errors = node.validate_before_node_run()

    assert errors is not None
    assert len(errors) == 1
    assert isinstance(errors[0], NodeError)
    assert str(errors[0]) == (
        "TOPAZ_LABS_API_KEY is not set. Add it in Settings → API Keys & Secrets, then run the node again."
    )
    assert [link.url for link in errors[0].links] == [KEY_LINK]
    assert not node.validate_before_workflow_run()
    with pytest.raises(NodeError, match="TOPAZ_LABS_API_KEY is not set"):
        node._get_api_key()


@pytest.mark.parametrize(("module_name", "class_name"), NODES)
def test_a_refused_key_links_to_settings_and_nothing_else(
    module_name: str, class_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = VIDEO_401 if _is_video(module_name) else IMAGE_401

    error = _fail(monkeypatch, module_name, class_name, (401, body))

    assert str(error) == (
        "Topaz Labs refused the API key. Update TOPAZ_LABS_API_KEY in Settings → API Keys & Secrets, "
        "then run the node again."
    )
    assert error.fields["status_code"] == 401
    assert error.fields.get("error_code") == body.get("errorCode")
    assert error.response == body
    assert [(link.label, link.url) for link in error.links] == [("Update the API key", KEY_LINK)]


@pytest.mark.parametrize(("module_name", "class_name"), [IMAGE_NODES[0], VIDEO_NODES[0]])
def test_a_403_is_not_a_refused_key(module_name: str, class_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """The 403 body is canned. It carries only a message."""
    error = _fail(monkeypatch, module_name, class_name, (403, {"message": "Plan limit reached"}))

    assert str(error) == "Plan limit reached"
    assert error.fields["status_code"] == 403
    assert error.links == []


def test_a_403_from_signed_storage_is_not_an_api_key_problem(monkeypatch: pytest.MonkeyPatch) -> None:
    denied = "<Error><Code>AccessDenied</Code></Error>"

    error = _fail(monkeypatch, *VIDEO_NODES[0], upload=(403, denied))

    assert "refused the API key" not in str(error)
    assert error.links == []
    assert error.fields == {"status_code": 403, "request_id": "r1"}
    assert error.response == {"body": denied}


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (requests.ConnectTimeout("slow"), "Topaz Labs did not answer in time. Run the node again."),
        (
            requests.ConnectionError("HTTPSConnectionPool(host='api.topazlabs.com')"),
            "Could not reach Topaz Labs. Check your internet connection and run the node again.",
        ),
    ],
)
def test_timeouts_and_connection_failures_get_short_messages(
    failure: Exception, message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert str(_fail(monkeypatch, *IMAGE_NODES[0], failure)) == message


def test_a_failed_image_job_carries_the_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    failed = {"status": "Failed", "message": "Image rejected"}

    error = _fail(monkeypatch, *IMAGE_NODES[2], status=(200, failed))

    assert str(error) == "Image rejected"
    assert error.fields == {"job_id": "p1"}
    assert error.response == failed


def test_an_image_job_that_outlasts_the_wait_limit_carries_the_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _network(monkeypatch, _route(False, status=(200, {"status": "Processing"})))

    with pytest.raises(NodeError) as raised:
        TopazClient("key").enhance_gen(b"x" * 200, poll_interval=0, max_wait_time=1)

    assert "did not finish the image within 1 seconds" in str(raised.value)
    assert raised.value.fields == {"job_id": "p1"}


def test_a_failed_video_job_carries_the_request_id(monkeypatch: pytest.MonkeyPatch) -> None:
    failed = {"status": "failed", "message": "Unsupported codec"}

    error = _fail(monkeypatch, *VIDEO_NODES[1], status=(200, failed))

    assert str(error) == "Unsupported codec"
    assert error.fields == {"request_id": "r1"}
    assert error.response == failed


@pytest.mark.parametrize(("module_name", "class_name"), VIDEO_NODES)
@pytest.mark.parametrize("minutes", [None, 5, 0.001])
def test_a_video_job_that_outlasts_the_wait_limit_names_the_timeout_parameter_in_minutes(
    module_name: str, class_name: str, minutes: float | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = _with_input(_node(module_name, class_name), module_name)
    if minutes is not None:
        _force(node, "processing_timeout", minutes)
    polls = []
    ticks = iter(range(0, 10**6, 100))
    fake_time = SimpleNamespace(time=lambda: next(ticks), strftime=time.strftime)
    if minutes != 0.001:
        monkeypatch.setattr(base_topaz_video_node, "time", fake_time)
    route = _route(True, status=(200, {"status": "processing"}))
    _network(monkeypatch, lambda r: polls.append(r.url) or route(r))

    error = _run(node)

    shown = 60 if minutes is None else minutes
    assert (
        str(error)
        == f"The video did not finish within {shown} minutes. Raise 'Timeout (minutes)' and run the node again."
    )
    assert error.fields == {"request_id": "r1"}
    # With the fake clock, 100 s per call: a 5 minute wait polls twice, an hour polls many times.
    if minutes == 5:
        assert len([u for u in polls if u.endswith("/status")]) == 2


@pytest.mark.parametrize(
    ("steps", "message", "fields"),
    [
        ({"create": (200, {"status": "ok"})}, "Topaz Labs did not return a request ID.", {}),
        ({"accept": (200, {"urls": []})}, "Topaz Labs did not return an upload URL.", {"request_id": "r1"}),
        ({"upload": (200, "")}, "Topaz Labs file storage did not return an ETag", {"request_id": "r1"}),
        ({"status": (200, {"status": "complete"})}, "Topaz Labs did not return a download URL.", {"request_id": "r1"}),
        ({"start": (200, {"queued": True})}, "Topaz Labs did not return a job ID.", {}),
        ({"download": (200, {"other": 1})}, "Topaz Labs did not return a download URL.", {"job_id": "p1"}),
    ],
)
def test_an_answer_missing_something_the_node_needs_carries_the_id(
    steps: dict[str, Any], message: str, fields: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    node_type = IMAGE_NODES[2] if "start" in steps or "download" in steps else VIDEO_NODES[1]

    error = _fail(monkeypatch, *node_type, **steps)

    assert str(error).startswith(message)
    assert error.fields == fields


@pytest.mark.parametrize(("module_name", "class_name"), VIDEO_NODES)
def test_a_stalled_video_download_reads_the_same_on_every_node(
    module_name: str, class_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The nodes download through `TopazClient.download_file`, so no raw requests timeout escapes."""
    error = _fail(monkeypatch, module_name, class_name, file=requests.ReadTimeout("stalled"))

    assert str(error) == "Topaz Labs file storage did not answer in time. Run the node again."
    assert error.fields == {"request_id": "r1"}


def test_a_failed_image_download_reports_the_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    error = _fail(monkeypatch, *IMAGE_NODES[2], file=(500, "oops"))

    assert error.fields == {"status_code": 500, "job_id": "p1"}


@pytest.mark.parametrize("body", ["<html>Oops</html>", "", [{"process_id": "p1"}]], ids=["html", "empty", "list"])
@pytest.mark.parametrize(
    ("node_type", "step"),
    [(IMAGE_NODES[2], "start"), (IMAGE_NODES[2], "status"), (VIDEO_NODES[0], "create"), (VIDEO_NODES[0], "status")],
)
def test_a_2xx_without_a_json_object_is_a_node_error(
    node_type: tuple[str, str], step: str, body: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = _fail(monkeypatch, *node_type, **{step: (200, body)})

    assert str(error) == "Topaz Labs sent a response the node could not read (HTTP 200)."
    assert error.fields["status_code"] == 200


@pytest.mark.parametrize(("module_name", "class_name"), IMAGE_NODES[:2])
def test_a_2xx_that_is_not_an_image_is_a_node_error(
    module_name: str, class_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    html = (200, "<html>Oops</html>", {"content-type": "text/html"})

    error = _fail(monkeypatch, module_name, class_name, html)

    assert str(error) == "Topaz Labs sent a response the node could not read (HTTP 200)."
    assert error.response == {"body": "<html>Oops</html>"}


@pytest.mark.parametrize(
    ("module_name", "class_name", "name", "label", "value"),
    [
        ("topaz_denoise_node", "TopazDenoiseNode", "strength", "Strength", 5.0),
        ("topaz_denoise_node", "TopazDenoiseNode", "minor_deblur", "Minor Deblur", -1.0),
        ("topaz_enhance_node", "TopazEnhanceNode", "fix_compression", "Fix Compression", 2.0),
        ("topaz_video_upscale_node", "TopazVideoUpscaleNode", "processing_timeout", "Timeout (minutes)", 500),
    ],
)
def test_an_out_of_range_value_names_the_label_and_carries_the_parameter(
    module_name: str, class_name: str, name: str, label: str, value: float
) -> None:
    node = _node(module_name, class_name)
    _force(node, name, value)

    errors = node.validate_before_node_run()

    assert errors is not None
    assert len(errors) == 1
    assert isinstance(errors[0], NodeError)
    assert str(errors[0]).startswith(f"'{label}' must be between ")
    assert str(errors[0]).endswith(f"It's set to {value}.")
    assert errors[0].fields == {"parameter": name}


@pytest.mark.parametrize(("module_name", "class_name"), NODES)
@pytest.mark.parametrize("value", [None, BlobArtifact(b"tiny")], ids=["missing", "empty"])
def test_a_missing_or_empty_input_names_the_parameter(module_name: str, class_name: str, value: Any) -> None:
    video = _is_video(module_name)
    node = _node(module_name, class_name)
    if value is not None:
        node.set_parameter_value("video_input" if video else "image_input", value)

    error = _run(node)

    label, name = ("Input Video", "video_input") if video else ("Input Image", "image_input")
    assert f"connected to '{label}'" in str(error)
    assert error.fields == {"parameter": name}
    assert name not in str(error)
