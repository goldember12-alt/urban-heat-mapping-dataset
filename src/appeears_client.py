from __future__ import annotations

import json
import logging
import os
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
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.city_id = city_id
        self.product = product


@dataclass(frozen=True)
class AppEEARSTaskResponse:
    task_id: str
    raw: dict[str, Any]


def read_auth_from_environment() -> AppEEARSAuthConfig:
    """Read AppEEARS authentication configuration from environment variables."""
    preflight = appeears_credential_preflight()
    if not preflight.is_configured:
        raise ValueError(preflight.message)

    token = os.getenv(APPEEARS_TOKEN_ENV)
    if token:
        return AppEEARSAuthConfig(token=token, username=None, password=None)

    username = os.getenv(EARTHDATA_USERNAME_ENV)
    password = os.getenv(EARTHDATA_PASSWORD_ENV)
    return AppEEARSAuthConfig(token=None, username=username, password=password)


def appeears_credential_preflight() -> AppEEARSCredentialPreflight:
    """Return whether AppEEARS credentials are configured and which env vars are missing."""
    token = os.getenv(APPEEARS_TOKEN_ENV)
    username = os.getenv(EARTHDATA_USERNAME_ENV)
    password = os.getenv(EARTHDATA_PASSWORD_ENV)

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
        result = self._request_json("POST", "/task", json=payload)
        if not isinstance(result, dict):
            raise AppEEARSRequestError("Task submission returned an unexpected response payload")

        task_id = result.get("task_id") or result.get("taskid") or result.get("task")
        if not isinstance(task_id, str) or not task_id:
            raise AppEEARSRequestError("Task submission returned no task_id")
        return AppEEARSTaskResponse(task_id=task_id, raw=result)

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

    def _request_json(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        try:
            response = self._session.request(
                method=method,
                url=self._api_url(path),
                headers=self._headers(),
                json=json,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise AppEEARSRequestError(f"AppEEARS API request failed for {method} {path}: {exc}") from exc

        if response.status_code >= 400:
            response_detail = _response_error_detail(response)
            if method.upper() == "POST" and path == "/task":
                city_id, product = _extract_submit_context(json)
                city_label = str(city_id) if city_id is not None else "unknown"
                product_label = product or "unknown"
                logger.error(
                    "AppEEARS task submission failed: status=%s city_id=%s product=%s response=%s",
                    response.status_code,
                    city_label,
                    product_label,
                    response_detail,
                )
                raise AppEEARSRequestError(
                    (
                        "AppEEARS task submission failed "
                        f"(status={response.status_code}, city_id={city_label}, product={product_label}): "
                        f"{response_detail}"
                    ),
                    status_code=response.status_code,
                    response_text=response_detail,
                    city_id=city_id,
                    product=product,
                )

            raise AppEEARSRequestError(
                f"AppEEARS API request failed for {method} {path}: status={response.status_code}, response={response_detail}",
                status_code=response.status_code,
                response_text=response_detail,
            )

        return response.json()


