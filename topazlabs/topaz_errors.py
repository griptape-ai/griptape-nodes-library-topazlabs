"""Errors raised by the Topaz Labs nodes.

Each builder returns a NodeError. The message tells the user what to do, and the status code, job or
request ID and the provider's response are attached as fields and response.
"""

import json
from typing import Any
from urllib.parse import quote

import requests
from constants import API_KEY_ENV_VAR
from griptape_nodes.exe_types.core_types import NodeError, NodeErrorLink

MAX_RESPONSE_BYTES = 8_000
MAX_BODY_TEXT = 2_000


def _api_key_link(label: str) -> NodeErrorLink:
    return NodeErrorLink(label=label, url=f"#settings-secrets?filter={quote(API_KEY_ENV_VAR)}")


def _article(noun: str) -> str:
    return "an" if noun[0] in "aeiou" else "a"


def missing_api_key_error() -> NodeError:
    """The API key secret is not set."""
    return NodeError(
        f"{API_KEY_ENV_VAR} is not set. Add it in Settings → API Keys & Secrets, then run the node again.",
        links=[_api_key_link("Add the API key")],
    )


def missing_input_error(label: str, kind: str) -> NodeError:
    """A required input has no value. `label` is the name the UI shows for the parameter."""
    return NodeError(
        f"No {kind} is connected to '{label}'. Connect {_article(kind)} {kind} and run the node again.",
        fields={"parameter": label},
    )


def unreadable_input_error(label: str, kind: str, reason: object) -> NodeError:
    """The value of an input could not be read."""
    return NodeError(
        f"Could not read the {kind} connected to '{label}': {reason}. Reconnect the {kind} and run the node again.",
        fields={"parameter": label},
    )


def empty_input_error(label: str, kind: str) -> NodeError:
    """The value of an input holds no usable data."""
    return NodeError(
        f"The {kind} connected to '{label}' is empty or too small to process. Connect a valid {kind}.",
        fields={"parameter": label},
    )


def out_of_range_error(label: str, value: float, low: float, high: float, parameter: str) -> NodeError:
    """A numeric input is outside its allowed range."""
    return NodeError(
        f"'{label}' must be between {low} and {high}. It's set to {value}.",
        fields={"parameter": parameter},
    )


def _response_body(response: requests.Response) -> dict[str, Any]:
    """The provider's response as a JSON-serializable dict under the size limit."""
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and len(json.dumps(body, default=str)) <= MAX_RESPONSE_BYTES:
        return body
    text = response.text or ""
    return {"body": text[:MAX_BODY_TEXT]}


def _provider_message(body: dict[str, Any]) -> str | None:
    message = body.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def http_error(response: requests.Response, *, request_id: str | None = None, job_id: str | None = None) -> NodeError:
    """A Topaz Labs API call returned an error status."""
    status_code = response.status_code
    body = _response_body(response)
    fields: dict[str, str | int | float | bool] = {"status_code": status_code}
    if request_id:
        fields["request_id"] = request_id
    if job_id:
        fields["job_id"] = job_id
    error_code = body.get("errorCode")
    if isinstance(error_code, str):
        fields["error_code"] = error_code

    links: list[NodeErrorLink] = []
    if status_code == 401:
        message = f"Topaz Labs refused the API key. Update {API_KEY_ENV_VAR} in Settings → API Keys & Secrets, then run the node again."
        links.append(_api_key_link("Update the API key"))
    elif status_code == 429:
        message = "Topaz Labs is rate-limiting requests. Wait a minute and run the node again."
    elif status_code >= 500:
        message = "Topaz Labs had a server error. Run the node again in a few minutes."
    else:
        message = _provider_message(body) or f"Topaz Labs rejected the request with status {status_code}."
    return NodeError(message, fields=fields, response=body, links=links)


def raise_for_status(response: requests.Response, *, request_id: str | None = None, job_id: str | None = None) -> None:
    """Raise a NodeError when a Topaz Labs API response is an error."""
    if not response.ok:
        raise http_error(response, request_id=request_id, job_id=job_id)


def storage_error(response: requests.Response, action: str, *, request_id: str | None = None) -> NodeError:
    """An upload to or download from Topaz Labs storage returned an error status."""
    fields: dict[str, str | int | float | bool] = {"status_code": response.status_code}
    if request_id:
        fields["request_id"] = request_id
    return NodeError(
        f"{action} failed with status {response.status_code}. Run the node again.",
        fields=fields,
        response={"body": (response.text or "")[:MAX_BODY_TEXT]},
    )


def timeout_error() -> NodeError:
    """A Topaz Labs API call did not answer in time."""
    return NodeError("Topaz Labs did not answer in time. Run the node again.")


def connection_error() -> NodeError:
    """Topaz Labs could not be reached."""
    return NodeError("Could not reach Topaz Labs. Check your internet connection and run the node again.")


def job_failed_error(
    message: str | None, status_response: dict[str, Any], *, request_id: str | None = None, job_id: str | None = None
) -> NodeError:
    """Topaz Labs reported that a job failed."""
    fields: dict[str, str | int | float | bool] = {}
    if request_id:
        fields["request_id"] = request_id
    if job_id:
        fields["job_id"] = job_id
    status = status_response.get("status")
    if isinstance(status, str):
        fields["status"] = status
    return NodeError(
        message or "Topaz Labs could not process the file. Check the input and run the node again.",
        fields=fields,
        response=status_response if len(json.dumps(status_response, default=str)) <= MAX_RESPONSE_BYTES else None,
    )


def job_timeout_error(seconds: int, *, request_id: str | None = None, job_id: str | None = None) -> NodeError:
    """A Topaz Labs job did not finish within the wait limit."""
    fields: dict[str, str | int | float | bool] = {}
    if request_id:
        fields["request_id"] = request_id
    if job_id:
        fields["job_id"] = job_id
    return NodeError(
        f"Topaz Labs did not finish within {seconds} seconds. Run the node again, or raise the timeout if the node has one.",
        fields=fields,
    )


def unexpected_response_error(
    problem: str, body: dict[str, Any] | None = None, *, request_id: str | None = None, job_id: str | None = None
) -> NodeError:
    """A Topaz Labs response is missing something the node needs."""
    fields: dict[str, str | int | float | bool] = {}
    if request_id:
        fields["request_id"] = request_id
    if job_id:
        fields["job_id"] = job_id
    return NodeError(
        f"Topaz Labs sent an unexpected response: {problem}. Run the node again.",
        fields=fields,
        response=body if body is not None and len(json.dumps(body, default=str)) <= MAX_RESPONSE_BYTES else None,
    )
