from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from src.config import (
    APPEEARS_BASE_URL,
    APPEEARS_TOKEN_ENV,
    EARTHDATA_PASSWORD_ENV,
    EARTHDATA_USERNAME_ENV,
)

logger = logging.getLogger(__name__)
_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_MAX_API_ATTEMPTS = 4


@dataclass(frozen=True)
class AppEEARSAuthConfig:
    token: str | None
    username: str | None
    password: str | None


@dataclass(frozen=True)
class AppEEARSCredentialPreflight:
    is_configured: bool
    missing_vars: tuple[str, ...]
    message: str


class AppEEARSRequestError(RuntimeError):
    """Raised for non-successful AppEEARS API requests."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_text: str = "",
        city_id: int | None = None,
        product: str | None = None,
        reason: str = "request_failed",
        recoverable: bool = False,
        task_name: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.city_id = city_id
        self.product = product
        self.reason = reason
        self.recoverable = recoverable
        self.task_name = task_name


@dataclass(frozen=True)
class AppEEARSTaskResponse:
    task_id: str
    raw: dict[str, Any]


def read_auth_from_environment() -> AppEEARSAuthConfig:
    """Read AppEEARS authentication configuration from environment variables."""
    preflight = appeears_credential_preflight()
    if not preflight.is_configured:
        raise ValueError(preflight.message)

    username = os.getenv(EARTHDATA_USERNAME_ENV)
    password = os.getenv(EARTHDATA_PASSWORD_ENV)
    if username and password:
        token = os.getenv(APPEEARS_TOKEN_ENV)
        if token:
            logger.info(
                "Both %s and Earthdata credentials are set; preferring Earthdata login to mint a fresh bearer token",
                APPEEARS_TOKEN_ENV,
            )
        return AppEEARSAuthConfig(token=None, username=username, password=password)

    token = os.getenv(APPEEARS_TOKEN_ENV)
    if token:
        return AppEEARSAuthConfig(token=token, username=None, password=None)

    return AppEEARSAuthConfig(token=None, username=username, password=password)


def appeears_credential_preflight() -> AppEEARSCredentialPreflight:
    """Return whether AppEEARS credentials are configured and which env vars are missing."""
    token = os.getenv(APPEEARS_TOKEN_ENV)
    username = os.getenv(EARTHDATA_USERNAME_ENV)
    password = os.getenv(EARTHDATA_PASSWORD_ENV)

    if username and password and token:
        return AppEEARSCredentialPreflight(
            is_configured=True,
            missing_vars=(),
            message=(
                f"Configured via {EARTHDATA_USERNAME_ENV} and {EARTHDATA_PASSWORD_ENV}; "
                f"{APPEEARS_TOKEN_ENV} is also set but will be ignored in favor of a fresh login token."
            ),
        )

    if token:
        return AppEEARSCredentialPreflight(
            is_configured=True,
            missing_vars=(),
            message=f"Configured via {APPEEARS_TOKEN_ENV}.",
        )

    if username and password:
        return AppEEARSCredentialPreflight(
            is_configured=True,
            missing_vars=(),
            message=f"Configured via {EARTHDATA_USERNAME_ENV} and {EARTHDATA_PASSWORD_ENV}.",
        )

    missing_vars: list[str] = []
    if not token:
        missing_vars.append(APPEEARS_TOKEN_ENV)
    if not username:
        missing_vars.append(EARTHDATA_USERNAME_ENV)
    if not password:
        missing_vars.append(EARTHDATA_PASSWORD_ENV)

    message = (
        "Missing AppEEARS credentials. Provide "
        f"{APPEEARS_TOKEN_ENV} or set both {EARTHDATA_USERNAME_ENV} and {EARTHDATA_PASSWORD_ENV}. "
        f"Missing env vars: {', '.join(missing_vars)}."
    )
    return AppEEARSCredentialPreflight(
        is_configured=False,
        missing_vars=tuple(missing_vars),
        message=message,
    )


def _normalize_iso_date(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d")
    return parsed.strftime("%m-%d-%Y")


def build_area_task_payload(
    task_name: str,
    product: str,
    layer: str,
    start_date: str,
    end_date: str,
    aoi_feature_collection: dict[str, Any],
) -> dict[str, Any]:
    """Build an AppEEARS area-task payload for one product/layer and AOI."""
    return {
        "task_type": "area",
        "task_name": task_name,
        "params": {
            "dates": [
                {
                    "startDate": _normalize_iso_date(start_date),
                    "endDate": _normalize_iso_date(end_date),
                }
            ],
            "layers": [
                {
                    "product": product,
                    "layer": layer,
                }
            ],
            "output": {
                "format": {"type": "geotiff"},
                "projection": "geographic",
            },
            "geo": aoi_feature_collection,
        },
    }


def _extract_submit_context(payload: dict[str, Any] | None) -> tuple[int | None, str | None]:
    if payload is None:
        return None, None

    try:
        layers = payload.get("params", {}).get("layers", [])
        product = layers[0].get("product") if layers and isinstance(layers[0], dict) else None
    except Exception:
        product = None

    city_id: int | None = None
    try:
        features = payload.get("params", {}).get("geo", {}).get("features", [])
        if features and isinstance(features[0], dict):
            city_id_value = features[0].get("properties", {}).get("city_id")
            if city_id_value is not None:
                city_id = int(city_id_value)
    except Exception:
        city_id = None

    return city_id, str(product) if isinstance(product, str) and product else None


def _extract_task_name(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    value = payload.get("task_name")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _response_error_detail(response: Any) -> str:
    try:
        body_json = response.json()
    except Exception:
        body_json = None

    if isinstance(body_json, dict):
        for key in ("message", "error", "detail", "details"):
            value = body_json.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:2000]
        return json.dumps(body_json)[:2000]

    text = str(getattr(response, "text", "") or "").strip()
    return text[:2000]


def _submission_failure_label(status_code: int, response_detail: str, auth_mode: str) -> str:
    detail = response_detail.lower()
    if status_code in {400, 422}:
        return "bad_payload"
    if status_code == 401:
        return "auth_failure"
    if status_code == 403:
        if auth_mode == APPEEARS_TOKEN_ENV:
            return "stale_or_invalid_token"
        if "permission" in detail or "read-protected" in detail or "forbidden" in detail:
            return "permission_or_eula_issue"
        return "forbidden_request"
    if status_code == 429:
        return "rate_limited"
    if status_code in {500, 502, 503, 504}:
        return "upstream_unavailable"
    return "request_failed"


def _request_exception_reason(exc: requests.RequestException) -> tuple[str, bool]:
    if isinstance(exc, requests.Timeout):
        return "request_timeout", True
    if isinstance(exc, requests.ConnectionError):
        return "connection_error", True
    return "request_failed", False


def _parse_task_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("task_id", "taskid", "task"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


class AppEEARSClient:
    """Thin AppEEARS API client with env-driven auth and simple task methods."""

    def __init__(
        self,
        auth: AppEEARSAuthConfig,
        base_url: str = APPEEARS_BASE_URL,
        timeout: int = 120,
        session: requests.Session | None = None,
    ) -> None:
        self._auth = auth
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._token: str | None = auth.token

    @classmethod
    def from_environment(
        cls,
        base_url: str = APPEEARS_BASE_URL,
        timeout: int = 120,
        session: requests.Session | None = None,
    ) -> "AppEEARSClient":
        auth = read_auth_from_environment()
        return cls(auth=auth, base_url=base_url, timeout=timeout, session=session)

    def _api_url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _headers(self) -> dict[str, str]:
        if not self._token:
            self.authenticate()
        return {"Authorization": f"Bearer {self._token}"}

    def _auth_mode(self) -> str:
        if self._auth.username and self._auth.password:
            return "earthdata_login"
        if self._token or self._auth.token:
            return APPEEARS_TOKEN_ENV
        return "unconfigured"

    def authenticate(self) -> str:
        """Return a bearer token, exchanging Earthdata user/pass if needed."""
        if self._token:
            return self._token

        if not self._auth.username or not self._auth.password:
            raise ValueError(
                "No token available and Earthdata credentials are missing. "
                "Set APPEEARS_API_TOKEN or EARTHDATA_USERNAME and EARTHDATA_PASSWORD."
            )

        logger.info("Authenticating to AppEEARS using Earthdata credentials from environment variables")
        try:
            response = self._session.post(
                self._api_url("/login"),
                auth=HTTPBasicAuth(self._auth.username, self._auth.password),
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise AppEEARSRequestError(f"AppEEARS authentication request failed: {exc}") from exc

        if response.status_code >= 400:
            raise AppEEARSRequestError(
                "AppEEARS authentication failed",
                status_code=response.status_code,
                response_text=response.text[:500],
            )

        payload = response.json()
        token = payload.get("token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise AppEEARSRequestError("AppEEARS authentication succeeded but no token was returned")

        self._token = token
        return token

    def submit_area_task(self, payload: dict[str, Any]) -> AppEEARSTaskResponse:
        """Submit an AppEEARS area task and return the task id."""
        task_name = _extract_task_name(payload)
        last_error: AppEEARSRequestError | None = None

        for attempt in range(1, _MAX_API_ATTEMPTS + 1):
            try:
                result = self._request_json("POST", "/task", json=payload, retryable=False)
                if not isinstance(result, dict):
                    raise AppEEARSRequestError(
                        "Task submission returned an unexpected response payload",
                        reason="unexpected_submit_payload",
                        recoverable=False,
                        task_name=task_name,
                    )

                task_id = _parse_task_id(result)
                if not task_id:
                    raise AppEEARSRequestError(
                        "Task submission returned no task_id",
                        reason="task_id_missing",
                        recoverable=False,
                        task_name=task_name,
                    )
                return AppEEARSTaskResponse(task_id=task_id, raw=result)
            except AppEEARSRequestError as exc:
                last_error = exc
                if task_name:
                    recovered = self.find_task_by_name(task_name)
                    recovered_task_id = _parse_task_id(recovered)
                    if recovered_task_id:
                        logger.warning(
                            "Recovered AppEEARS task after submit error by reusing task_name=%s task_id=%s reason=%s",
                            task_name,
                            recovered_task_id,
                            exc.reason,
                        )
                        return AppEEARSTaskResponse(task_id=recovered_task_id, raw=recovered)

                retryable_http_error = exc.status_code in _RETRYABLE_STATUS_CODES and not exc.recoverable
                if retryable_http_error and attempt < _MAX_API_ATTEMPTS:
                    logger.warning(
                        "AppEEARS submit failed for task_name=%s on attempt %s/%s with status=%s; retrying",
                        task_name or "unknown",
                        attempt,
                        _MAX_API_ATTEMPTS,
                        exc.status_code,
                    )
                    time.sleep(2 ** (attempt - 1))
                    continue

                if exc.recoverable and task_name:
                    raise AppEEARSRequestError(
                        (
                            f"{exc} Follow-up lookup by task_name={task_name} found no matching task, "
                            "so submission state remains unknown. Rerun with the same dates/city to retry safely."
                        ),
                        status_code=exc.status_code,
                        response_text=exc.response_text,
                        city_id=exc.city_id,
                        product=exc.product,
                        reason=exc.reason,
                        recoverable=True,
                        task_name=task_name,
                    ) from exc
                raise

        if last_error is not None:  # pragma: no cover
            raise last_error
        raise AppEEARSRequestError("Task submission failed without a response")  # pragma: no cover

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Fetch task status payload for an existing AppEEARS task."""
        payload = self._request_json("GET", f"/task/{task_id}")
        if not isinstance(payload, dict):
            raise AppEEARSRequestError("Unexpected task-status response from AppEEARS")
        return payload

    def list_bundle_files(self, task_id: str) -> list[dict[str, Any]]:
        """List downloadable bundle files for a completed task."""
        payload = self._request_json("GET", f"/bundle/{task_id}")
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            files = payload.get("files")
            if isinstance(files, list):
                return [x for x in files if isinstance(x, dict)]
        raise AppEEARSRequestError("Unexpected bundle list response from AppEEARS")

    def list_tasks(self) -> list[dict[str, Any]]:
        """Return the visible AppEEARS task list when the API exposes it."""
        payload = self._request_json("GET", "/task")
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("tasks", "items"):
                values = payload.get(key)
                if isinstance(values, list):
                    return [item for item in values if isinstance(item, dict)]
        raise AppEEARSRequestError(
            "Unexpected task-list response from AppEEARS",
            reason="unexpected_task_list_payload",
            recoverable=True,
        )

    def find_task_by_name(self, task_name: str) -> dict[str, Any] | None:
        """Best-effort recovery helper for ambiguous submit outcomes."""
        if not task_name.strip():
            return None
        try:
            tasks = self.list_tasks()
        except AppEEARSRequestError as exc:
            logger.warning("Task lookup by name=%s failed after submit ambiguity: %s", task_name, exc)
            return None

        matches = [
            item
            for item in tasks
            if str(item.get("task_name") or item.get("taskName") or "").strip() == task_name
        ]
        if not matches:
            return None
        return matches[-1]

    def download_bundle_file(self, task_id: str, file_id: str, destination: Path) -> Path:
        """Download one bundle file to disk (new files only)."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = destination.with_suffix(destination.suffix + ".part")

        try:
            response = self._session.get(
                self._api_url(f"/bundle/{task_id}/{file_id}"),
                headers=self._headers(),
                stream=True,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise AppEEARSRequestError(f"File download failed for file_id={file_id}: {exc}") from exc

        if response.status_code >= 400:
            raise AppEEARSRequestError(
                f"File download failed for file_id={file_id}",
                status_code=response.status_code,
                response_text=response.text[:500],
            )

        with temp_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

        temp_path.replace(destination)
        return destination

    def _request_json(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        *,
        retryable: bool = True,
    ) -> Any:
        for attempt in range(1, _MAX_API_ATTEMPTS + 1):
            try:
                response = self._session.request(
                    method=method,
                    url=self._api_url(path),
                    headers=self._headers(),
                    json=json,
                    timeout=self._timeout,
                )
            except requests.RequestException as exc:
                reason, recoverable = _request_exception_reason(exc)
                if retryable and recoverable and attempt < _MAX_API_ATTEMPTS:
                    logger.warning(
                        "AppEEARS API request retrying method=%s path=%s attempt=%s/%s reason=%s error=%s",
                        method,
                        path,
                        attempt,
                        _MAX_API_ATTEMPTS,
                        reason,
                        exc,
                    )
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise AppEEARSRequestError(
                    f"AppEEARS API request failed for {method} {path}: {exc}",
                    reason=reason,
                    recoverable=recoverable,
                    task_name=_extract_task_name(json),
                ) from exc

            if response.status_code >= 400:
                response_detail = _response_error_detail(response)
                if response.status_code in _RETRYABLE_STATUS_CODES and retryable and attempt < _MAX_API_ATTEMPTS:
                    logger.warning(
                        "AppEEARS API request retrying method=%s path=%s attempt=%s/%s status=%s",
                        method,
                        path,
                        attempt,
                        _MAX_API_ATTEMPTS,
                        response.status_code,
                    )
                    time.sleep(2 ** (attempt - 1))
                    continue

                if method.upper() == "POST" and path == "/task":
                    city_id, product = _extract_submit_context(json)
                    city_label = str(city_id) if city_id is not None else "unknown"
                    product_label = product or "unknown"
                    auth_mode = self._auth_mode()
                    failure_label = _submission_failure_label(
                        status_code=response.status_code,
                        response_detail=response_detail,
                        auth_mode=auth_mode,
                    )
                    hint = ""
                    if failure_label == "stale_or_invalid_token":
                        hint = (
                            f" Unset {APPEEARS_TOKEN_ENV} or provide {EARTHDATA_USERNAME_ENV}/{EARTHDATA_PASSWORD_ENV} "
                            "so the client can mint a fresh bearer token."
                        )
                    elif failure_label == "permission_or_eula_issue":
                        hint = " Confirm the Earthdata/AppEEARS account has accepted required terms and can submit this product in the web UI."
                    elif failure_label == "bad_payload":
                        hint = " Verify the product/layer/date/AOI payload against the AppEEARS product catalog."
                    logger.error(
                        "AppEEARS task submission failed: label=%s status=%s auth_mode=%s city_id=%s product=%s response=%s",
                        failure_label,
                        response.status_code,
                        auth_mode,
                        city_label,
                        product_label,
                        response_detail,
                    )
                    raise AppEEARSRequestError(
                        (
                            f"AppEEARS task submission failed [{failure_label}] "
                            f"(status={response.status_code}, auth_mode={auth_mode}, city_id={city_label}, product={product_label}): "
                            f"{response_detail}{hint}"
                        ),
                        status_code=response.status_code,
                        response_text=response_detail,
                        city_id=city_id,
                        product=product,
                        reason=failure_label,
                        recoverable=response.status_code in _RETRYABLE_STATUS_CODES,
                        task_name=_extract_task_name(json),
                    )

                raise AppEEARSRequestError(
                    f"AppEEARS API request failed for {method} {path}: status={response.status_code}, response={response_detail}",
                    status_code=response.status_code,
                    response_text=response_detail,
                    reason="request_failed",
                    recoverable=response.status_code in _RETRYABLE_STATUS_CODES,
                    task_name=_extract_task_name(json),
                )

            try:
                return response.json()
            except ValueError as exc:
                if retryable and attempt < _MAX_API_ATTEMPTS:
                    logger.warning(
                        "AppEEARS API request returned invalid JSON for method=%s path=%s attempt=%s/%s; retrying",
                        method,
                        path,
                        attempt,
                        _MAX_API_ATTEMPTS,
                    )
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise AppEEARSRequestError(
                    f"AppEEARS API request returned invalid JSON for {method} {path}: {_response_error_detail(response)}",
                    status_code=response.status_code,
                    response_text=_response_error_detail(response),
                    reason="invalid_json_response",
                    recoverable=True,
                    task_name=_extract_task_name(json),
                ) from exc

        raise AppEEARSRequestError(
            f"AppEEARS API request exhausted retries for {method} {path}",
            reason="request_retries_exhausted",
            recoverable=True,
            task_name=_extract_task_name(json),
        )  # pragma: no cover


