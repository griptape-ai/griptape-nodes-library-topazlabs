"""Errors the Topaz Labs nodes raise beyond what `NodeError` builds itself.

A missing or refused API key and a failed HTTP call come from `NodeError.from_missing_secret` and
`NodeError.from_request_exception`. This module covers bad inputs and jobs that end without a result.
"""

from __future__ import annotations

from typing import Any

from griptape_nodes.exe_types.core_types import NodeError

PROVIDER = "Topaz Labs"

Fields = dict[str, str | int | float | bool]


def missing_input_error(kind: str, label: str, parameter: str) -> NodeError:
    """A required input has no value. `label` is what the UI shows, `parameter` the node's own name."""
    article = "an" if kind[0] in "aeiou" else "a"
    return NodeError(
        f"No {kind} is connected to '{label}'. Connect {article} {kind} and run the node again.",
        fields={"parameter": parameter},
    )


def unusable_input_error(kind: str, label: str, parameter: str, reason: object) -> NodeError:
    """An input has a value the node cannot read or use."""
    return NodeError(
        f"Could not use the {kind} connected to '{label}': {reason}. Reconnect the {kind} and run the node again.",
        fields={"parameter": parameter},
    )


def out_of_range_error(label: str, parameter: str, value: float, low: float, high: float) -> NodeError:
    """A numeric input is outside its allowed range."""
    return NodeError(
        f"'{label}' must be between {low} and {high}. It's set to {value}.",
        fields={"parameter": parameter},
    )


def job_error(message: str, *, response: dict[str, Any] | None = None, **ids: str | None) -> NodeError:
    """A job failed, ran past the wait limit, or got an answer without something the node needs.

    `ids` holds `job_id` (image API) or `request_id` (video API). Unset ones are left out.
    """
    fields: Fields = {name: value for name, value in ids.items() if value}
    return NodeError(message, fields=fields, response=response)
