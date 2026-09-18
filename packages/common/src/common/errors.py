"""Rejection codes shared by the orchestrator and every backend.

`model_not_found` (404): the request is wrong, edit it. `model_unavailable`
(503): the request is fine, the cluster is not, retry. Sharing one code between
the two would have people editing correct requests.
"""

from typing import Literal

ErrorCode = Literal["model_not_found", "model_unavailable"]

MODEL_NOT_FOUND: ErrorCode = "model_not_found"
MODEL_UNAVAILABLE: ErrorCode = "model_unavailable"
