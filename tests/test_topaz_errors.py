"""Tests for the errors the Topaz Labs nodes raise."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import requests
from griptape.artifacts import BlobArtifact, ImageArtifact
from griptape_nodes.exe_types.core_types import NodeError
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
from topaz_creative_enhance_node import TopazCreativeEnhanceNode
from topaz_denoise_node import TopazDenoiseNode
from topaz_enhance_node import TopazEnhanceNode
from topaz_frame_interpolation_node import TopazFrameInterpolationNode
from topaz_video_denoise_node import TopazVideoDenoiseNode
from topaz_video_upscale_node import TopazVideoUpscaleNode

LIBRARY_DIR = Path(__file__).resolve().parent.parent / "topazlabs"
NODE_FILES = sorted(p.name for p in LIBRARY_DIR.glob("*.py") if p.name != "__init__.py")

KEY_LINK = "#settings-secrets?filter=TOPAZ_LABS_API_KEY"
IMAGE_BYTES = b"i" * 200
VIDEO_BYTES = b"v" * 2000

Responder = Callable[[requests.PreparedRequest], requests.Response | Exception]


def _response(status: int, *, body: Any = None, text: str = "", headers: dict[str, str] | None = None):
    response = requests.Response()
    response.status_code = status
    response._content = (json.dumps(body) if body is not None else text).encode()
    response.headers.update(headers or {"content-type": "application/json"})
    return response


class FakeHttp:
    """Answers every requests call through one responder."""

    def __init__(self) -> None:
        self.responder: Responder = lambda _r: _response(500)


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch) -> FakeHttp:
    """Fake the network at the adapter that every requests call goes through."""
    fake = FakeHttp()

    def send(_self: Any, request: requests.PreparedRequest, **_: Any) -> requests.Response:
        result = fake.responder(request)
        if isinstance(result, Exception):
            raise result
        result.url = request.url
        result.request = request
        return result

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    async def no_sleep(_s: float) -> None:
        return None

    monkeypatch.setattr("asyncio.sleep", no_sleep)
    return fake


def _respond(http: FakeHttp, responder: Responder) -> None:
    http.responder = responder


@pytest.fixture(autouse=True)
def api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSecrets:
        def get_secret(self, _name: str) -> str:
            return "key"

    monkeypatch.setattr(GriptapeNodes, "SecretsManager", lambda: FakeSecrets())


def _run(node: Any) -> None:
    asyncio.run(node._process_async())


def _image_node(cls: type) -> Any:
    node = cls("Node")
    node.set_parameter_value("image_input", ImageArtifact(IMAGE_BYTES, format="png", width=1, height=1))
    return node


def _video_node(cls: type) -> Any:
    node = cls("Node")
    node.parameter_values["video_input"] = BlobArtifact(VIDEO_BYTES)
    return node


def _raise_from_run(node: Any) -> NodeError:
    with pytest.raises(NodeError) as raised:
        _run(node)
    return raised.value


@pytest.mark.parametrize("file_name", NODE_FILES)
def test_node_file_loads_the_way_the_engine_loads_it(file_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """The engine loads each file alone with the library folder on sys.path and no parent package."""
    monkeypatch.setattr(sys, "path", [str(LIBRARY_DIR), *sys.path])
    for name in [*sys.modules, "topazlabs"]:
        if name == "topazlabs" or name.startswith("topazlabs."):
            monkeypatch.setitem(sys.modules, name, None)
    spec = importlib.util.spec_from_file_location(f"engine_loaded_{file_name[:-3]}", LIBRARY_DIR / file_name)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)

    spec.loader.exec_module(module)


# --- API key ---


def test_missing_api_key_links_to_the_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoSecrets:
        def get_secret(self, _name: str) -> None:
            return None

    monkeypatch.setattr(GriptapeNodes, "SecretsManager", lambda: NoSecrets())

    errors = TopazDenoiseNode("Node").validate_before_node_run()

    assert errors is not None
    assert len(errors) == 1
    error = errors[0]
    assert isinstance(error, NodeError)
    assert (
        str(error) == "TOPAZ_LABS_API_KEY is not set. Add it in Settings → API Keys & Secrets, then run the node again."
    )
    assert [(link.label, link.url) for link in error.links] == [("Add the API key", KEY_LINK)]


def test_missing_api_key_is_reported_by_the_video_node_too(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoSecrets:
        def get_secret(self, _name: str) -> None:
            return None

    monkeypatch.setattr(GriptapeNodes, "SecretsManager", lambda: NoSecrets())

    errors = TopazVideoUpscaleNode("Node").validate_before_node_run()

    assert errors is not None
    assert [link.url for link in errors[0].links] == [KEY_LINK]


@pytest.mark.parametrize(
    ("node_class", "parameter", "bad_value"),
    [
        (TopazDenoiseNode, "strength", 5.0),
        (TopazEnhanceNode, "sharpen", 1000.0),
        (TopazVideoUpscaleNode, "processing_timeout", 1),
    ],
)
def test_a_missing_key_is_the_only_problem_reported(
    monkeypatch: pytest.MonkeyPatch, node_class: type, parameter: str, bad_value: float
) -> None:
    class NoSecrets:
        def get_secret(self, _name: str) -> None:
            return None

    monkeypatch.setattr(GriptapeNodes, "SecretsManager", lambda: NoSecrets())
    node = node_class("Node")
    node.parameter_values[parameter] = bad_value

    errors = node.validate_before_node_run()

    assert errors is not None
    assert len(errors) == 1
    assert "TOPAZ_LABS_API_KEY is not set" in str(errors[0])


def test_refused_api_key_links_to_update_the_secret(http: FakeHttp) -> None:
    _respond(http, lambda _r: _response(401, body={"message": "Invalid authentication token"}))

    error = _raise_from_run(_image_node(TopazDenoiseNode))

    assert str(error) == (
        "Topaz Labs refused the API key. Update TOPAZ_LABS_API_KEY in Settings → API Keys & Secrets, "
        "then run the node again."
    )
    assert error.fields == {"status_code": 401}
    assert error.response == {"message": "Invalid authentication token"}
    assert [(link.label, link.url) for link in error.links] == [("Update the API key", KEY_LINK)]


# --- Validation ---


@pytest.mark.parametrize("node_class", [TopazDenoiseNode, TopazVideoUpscaleNode])
def test_nothing_is_checked_before_the_flow_starts(monkeypatch: pytest.MonkeyPatch, node_class: type) -> None:
    """A problem found before the flow starts is a toast with no link and no error on a node's header.

    The key and the values are checked when the node runs instead.
    """

    class NoSecrets:
        def get_secret(self, _name: str) -> None:
            return None

    monkeypatch.setattr(GriptapeNodes, "SecretsManager", lambda: NoSecrets())
    node = node_class("Node")
    node.parameter_values["strength"] = 5.0

    assert not node.validate_before_workflow_run()


def test_node_validation_names_the_parameter_and_range() -> None:
    node = TopazDenoiseNode("Node")
    node.parameter_values["strength"] = 5.0

    errors = node.validate_before_node_run()

    assert errors is not None
    assert len(errors) == 1
    assert isinstance(errors[0], NodeError)
    assert str(errors[0]) == "'Strength' must be between 0.01 and 1.0. It's set to 5.0."
    assert errors[0].fields == {"parameter": "strength"}


def test_enhance_validation_uses_the_label_the_ui_shows() -> None:
    node = TopazEnhanceNode("Node")
    node.parameter_values["fix_compression"] = 9.0

    errors = node.validate_before_node_run()

    assert errors is not None
    assert str(errors[0]).startswith("'Fix Compression' must be between")


def test_video_validation_reports_the_timeout_range() -> None:
    node = TopazVideoDenoiseNode("Node")
    node.parameter_values["processing_timeout"] = 500

    errors = node.validate_before_node_run()

    assert errors is not None
    assert str(errors[0]) == "'Timeout (minutes)' must be between 5 and 180. It's set to 500."


# --- Inputs ---


def test_missing_image_names_the_parameter() -> None:
    error = _raise_from_run(TopazEnhanceNode("Node"))

    assert str(error) == "No image is connected to 'Input Image'. Connect an image and run the node again."
    assert error.fields == {"parameter": "image_input"}


def test_missing_video_names_the_parameter() -> None:
    error = _raise_from_run(TopazVideoUpscaleNode("Node"))

    assert error.fields == {"parameter": "video_input"}
    assert "'Input Video'" in str(error)


def test_tiny_image_is_rejected() -> None:
    node = TopazDenoiseNode("Node")
    node.set_parameter_value("image_input", ImageArtifact(b"tiny", format="png", width=1, height=1))

    error = _raise_from_run(node)

    assert str(error) == "The image connected to 'Input Image' is empty or too small to process. Connect a valid image."


# --- Image API failures ---


def test_rate_limit_message_gives_the_wait_advice(http: FakeHttp) -> None:
    _respond(http, lambda _r: _response(429, body={"message": "Too many requests"}))

    error = _raise_from_run(_image_node(TopazEnhanceNode))

    assert str(error) == "Topaz Labs is rate-limiting requests. Wait a minute and run the node again."
    assert error.fields == {"status_code": 429}
    assert error.response == {"message": "Too many requests"}


def test_server_error_attaches_the_response(http: FakeHttp) -> None:
    _respond(http, lambda _r: _response(502, text="<html>Bad gateway</html>"))

    error = _raise_from_run(_image_node(TopazEnhanceNode))

    assert str(error) == "Topaz Labs had a server error. Run the node again in a few minutes."
    assert error.fields == {"status_code": 502}
    assert error.response == {"body": "<html>Bad gateway</html>"}


def test_client_error_uses_the_providers_message_and_error_code(http: FakeHttp) -> None:
    body = {"message": "Image dimensions exceed the limit", "errorCode": "IMAGE_TOO_LARGE"}
    _respond(http, lambda _r: _response(400, body=body))

    error = _raise_from_run(_image_node(TopazDenoiseNode))

    assert str(error) == "Image dimensions exceed the limit"
    assert error.fields == {"status_code": 400, "error_code": "IMAGE_TOO_LARGE"}
    assert error.response == body
    assert error.links == []


def test_timeout_and_connection_failures_are_reported(http: FakeHttp) -> None:
    _respond(http, lambda _r: requests.exceptions.ConnectionError("boom"))
    assert str(_raise_from_run(_image_node(TopazDenoiseNode))).startswith("Could not reach Topaz Labs.")

    _respond(http, lambda _r: requests.exceptions.Timeout("slow"))
    assert (
        str(_raise_from_run(_image_node(TopazDenoiseNode))) == "Topaz Labs did not answer in time. Run the node again."
    )


def test_non_image_reply_is_reported(http: FakeHttp) -> None:
    _respond(http, lambda _r: _response(200, text="hello", headers={"content-type": "text/plain"}))

    error = _raise_from_run(_image_node(TopazDenoiseNode))

    assert (
        str(error)
        == "Topaz Labs sent an unexpected response: expected an image but received 'text/plain'. Run the node again."
    )


def test_status_text_keeps_the_failure_for_the_status_output(http: FakeHttp) -> None:
    _respond(http, lambda _r: _response(429, body={}))
    node = _image_node(TopazDenoiseNode)

    _raise_from_run(node)

    assert "rate-limiting" in node.get_parameter_value("status")


def test_generative_job_failure_carries_the_job_id_and_status(http: FakeHttp) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        if request.method == "POST":
            return _response(200, body={"process_id": "proc-1"})
        return _response(200, body={"status": "Failed", "message": "The image could not be processed"})

    _respond(http, respond)

    error = _raise_from_run(_image_node(TopazCreativeEnhanceNode))

    assert str(error) == "The image could not be processed"
    assert error.fields == {"job_id": "proc-1", "status": "Failed"}
    assert error.response == {"status": "Failed", "message": "The image could not be processed"}


def test_generative_status_check_failure_carries_the_job_id(http: FakeHttp) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        if request.method == "POST":
            return _response(200, body={"process_id": "proc-2"})
        return _response(404, body={"message": "Process not found"})

    _respond(http, respond)

    error = _raise_from_run(_image_node(TopazCreativeEnhanceNode))

    assert str(error) == "Process not found"
    assert error.fields == {"status_code": 404, "job_id": "proc-2"}


def test_generative_job_without_an_id_is_reported(http: FakeHttp) -> None:
    _respond(http, lambda _r: _response(200, body={"unexpected": True}))

    error = _raise_from_run(_image_node(TopazCreativeEnhanceNode))

    assert str(error) == "Topaz Labs sent an unexpected response: the response has no process_id. Run the node again."
    assert error.response == {"unexpected": True}


def test_generative_job_that_never_finishes_times_out(http: FakeHttp, monkeypatch: pytest.MonkeyPatch) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        if request.method == "POST":
            return _response(200, body={"process_id": "proc-3"})
        return _response(200, body={"status": "Processing"})

    _respond(http, respond)
    clock = iter(range(0, 10_000, 100))
    monkeypatch.setattr("time.time", lambda: next(clock))

    error = _raise_from_run(_image_node(TopazCreativeEnhanceNode))

    assert str(error).startswith("Topaz Labs did not finish within 300 seconds.")
    assert error.fields == {"job_id": "proc-3"}


# --- Video API failures ---


@pytest.mark.parametrize("node_class", [TopazVideoUpscaleNode, TopazVideoDenoiseNode, TopazFrameInterpolationNode])
def test_video_job_failure_carries_the_request_id(http: FakeHttp, node_class: type) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        url = request.url or ""
        if request.method == "POST":
            return _response(200, body={"requestId": "req-9"})
        if url.endswith("/accept"):
            return _response(200, body={"urls": ["https://storage.example/upload"]})
        if "storage.example" in url:
            return _response(200, headers={"ETag": '"abc"'})
        if url.endswith("/complete-upload"):
            return _response(200, body={})
        return _response(200, body={"status": "failed", "message": "Unsupported codec"})

    _respond(http, respond)

    error = _raise_from_run(_video_node(node_class))

    assert str(error) == "Unsupported codec"
    assert error.fields == {"request_id": "req-9", "status": "failed"}
    assert error.response == {"status": "failed", "message": "Unsupported codec"}


def test_video_request_refused_key_has_the_update_link(http: FakeHttp) -> None:
    body = {"message": "Unauthorized", "errorCode": "UNAUTHORIZED"}
    _respond(http, lambda _r: _response(401, body=body))

    error = _raise_from_run(_video_node(TopazVideoUpscaleNode))

    assert error.fields == {"status_code": 401, "error_code": "UNAUTHORIZED"}
    assert error.response == body
    assert [(link.label, link.url) for link in error.links] == [("Update the API key", KEY_LINK)]


def test_video_accept_failure_carries_the_request_id(http: FakeHttp) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        if request.method == "POST":
            return _response(200, body={"requestId": "req-4"})
        return _response(409, body={"message": "Request already accepted"})

    _respond(http, respond)

    error = _raise_from_run(_video_node(TopazVideoDenoiseNode))

    assert str(error) == "Request already accepted"
    assert error.fields == {"status_code": 409, "request_id": "req-4"}


def test_video_upload_failure_is_reported(http: FakeHttp) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        url = request.url or ""
        if request.method == "POST":
            return _response(200, body={"requestId": "req-5"})
        if url.endswith("/accept"):
            return _response(200, body={"urls": ["https://storage.example/upload"]})
        return _response(403, text="<Error>AccessDenied</Error>")

    _respond(http, respond)

    error = _raise_from_run(_video_node(TopazVideoUpscaleNode))

    assert str(error) == "Uploading the video failed with status 403. Run the node again."
    assert error.fields == {"status_code": 403}
    assert error.response == {"body": "<Error>AccessDenied</Error>"}


def test_video_completed_job_without_a_download_url_is_reported(http: FakeHttp) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        url = request.url or ""
        if request.method == "POST":
            return _response(200, body={"requestId": "req-6"})
        if url.endswith("/accept"):
            return _response(200, body={"urls": ["https://storage.example/upload"]})
        if "storage.example" in url:
            return _response(200, headers={"ETag": '"abc"'})
        if url.endswith("/complete-upload"):
            return _response(200, body={})
        return _response(200, body={"status": "complete"})

    _respond(http, respond)

    error = _raise_from_run(_video_node(TopazVideoUpscaleNode))

    assert (
        str(error)
        == "Topaz Labs sent an unexpected response: the completed job has no download URL. Run the node again."
    )
    assert error.fields == {"request_id": "req-6"}
    assert error.response == {"status": "complete"}


def _completed_video_job(download: Any) -> Responder:
    """A video job that completes, with `download` answering the presigned download URL."""

    def respond(request: requests.PreparedRequest) -> requests.Response | Exception:
        url = request.url or ""
        if "download.example" in url:
            return download
        if request.method == "POST":
            return _response(200, body={"requestId": "req-7"})
        if url.endswith("/accept"):
            return _response(200, body={"urls": ["https://storage.example/upload"]})
        if "storage.example" in url:
            return _response(200, headers={"ETag": '"abc"'})
        if url.endswith("/complete-upload"):
            return _response(200, body={})
        return _response(200, body={"status": "complete", "download": {"url": "https://download.example/out.mp4"}})

    return respond


VIDEO_NODES = [TopazVideoUpscaleNode, TopazVideoDenoiseNode, TopazFrameInterpolationNode]


@pytest.mark.parametrize("node_class", VIDEO_NODES)
def test_video_download_that_stalls_is_reported_as_a_timeout(http: FakeHttp, node_class: type) -> None:
    _respond(http, _completed_video_job(requests.exceptions.Timeout("Read timed out")))

    error = _raise_from_run(_video_node(node_class))

    assert str(error) == "Topaz Labs did not answer in time. Run the node again."


@pytest.mark.parametrize("node_class", VIDEO_NODES)
def test_video_download_that_cannot_connect_is_reported_as_unreachable(http: FakeHttp, node_class: type) -> None:
    _respond(http, _completed_video_job(requests.exceptions.ConnectionError("refused")))

    error = _raise_from_run(_video_node(node_class))

    assert str(error).startswith("Could not reach Topaz Labs.")


@pytest.mark.parametrize("node_class", VIDEO_NODES)
def test_video_download_failure_carries_the_status_and_request_id(http: FakeHttp, node_class: type) -> None:
    _respond(http, _completed_video_job(_response(403, text="expired")))

    error = _raise_from_run(_video_node(node_class))

    assert str(error) == "Downloading the processed video failed with status 403. Run the node again."
    assert error.fields == {"status_code": 403, "request_id": "req-7"}
    assert error.response == {"body": "expired"}


def test_generative_download_failure_reports_the_job_id_not_a_request_id(http: FakeHttp) -> None:
    def respond(request: requests.PreparedRequest) -> requests.Response:
        url = request.url or ""
        if "download.example" in url:
            return _response(403, text="expired")
        if request.method == "POST":
            return _response(200, body={"process_id": "proc-5"})
        if "/download/" in url:
            return _response(200, body={"download_url": "https://download.example/out.png"})
        return _response(200, body={"status": "Completed"})

    _respond(http, respond)

    error = _raise_from_run(_image_node(TopazCreativeEnhanceNode))

    assert str(error) == "Downloading the processed image failed with status 403. Run the node again."
    assert error.fields == {"status_code": 403, "job_id": "proc-5"}
