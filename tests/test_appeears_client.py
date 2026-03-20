import pytest
import requests

from src.appeears_client import (
    AppEEARSAuthConfig,
    AppEEARSClient,
    AppEEARSRequestError,
    appeears_credential_preflight,
    build_area_task_payload,
    read_auth_from_environment,
)


class _FakeResponse:
    def __init__(self, status_code: int, json_payload):
        self.status_code = status_code
        self._json_payload = json_payload
        self.text = str(json_payload)

    def json(self):
        return self._json_payload


class _FakeSession:
    def __init__(self, response: _FakeResponse):
        self._response = response

    def request(self, method, url, headers=None, json=None, timeout=None):
        return self._response


class _SequenceSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, json=None, timeout=None):
        self.calls.append({"method": method, "url": url, "json": json})
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_read_auth_from_environment_prefers_earthdata_credentials_over_static_token(monkeypatch):
    monkeypatch.setenv("APPEEARS_API_TOKEN", "stale-token")
    monkeypatch.setenv("EARTHDATA_USERNAME", "user")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "pass")

    auth = read_auth_from_environment()
    preflight = appeears_credential_preflight()

    assert auth.token is None
    assert auth.username == "user"
    assert auth.password == "pass"
    assert "ignored in favor of a fresh login token" in preflight.message


def test_build_area_task_payload_converts_cli_dates_to_appeears_format():
    aoi = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"city_id": 1},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]],
                },
            }
        ],
    }

    payload = build_area_task_payload(
        task_name="ndvi_phoenix_2023",
        product="MOD13A1.061",
        layer="500m_16_days_NDVI",
        start_date="2023-05-01",
        end_date="2023-08-31",
        aoi_feature_collection=aoi,
    )

    assert payload["task_type"] == "area"
    assert payload["task_name"] == "ndvi_phoenix_2023"
    assert payload["params"]["layers"][0]["product"] == "MOD13A1.061"
    assert payload["params"]["layers"][0]["layer"] == "500m_16_days_NDVI"
    assert payload["params"]["dates"][0]["startDate"] == "05-01-2023"
    assert payload["params"]["dates"][0]["endDate"] == "08-31-2023"
    assert payload["params"]["geo"]["type"] == "FeatureCollection"


def test_build_area_task_payload_rejects_mm_dd_yyyy_cli_input():
    with pytest.raises(ValueError):
        build_area_task_payload(
            task_name="ndvi_phoenix_2023",
            product="MOD13A1.061",
            layer="500m_16_days_NDVI",
            start_date="05-01-2023",
            end_date="08-31-2023",
            aoi_feature_collection={"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"city_id": 1}, "geometry": {"type": "Polygon", "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]]}}]},
        )


def test_submit_task_error_includes_status_response_city_and_product():
    response = _FakeResponse(
        status_code=400,
        json_payload={"message": "Invalid layer selection"},
    )
    client = AppEEARSClient(
        auth=AppEEARSAuthConfig(token="test-token", username=None, password=None),
        session=_FakeSession(response),
    )

    payload = build_area_task_payload(
        task_name="ndvi_phoenix_2023",
        product="MOD13A1.061",
        layer="500m_16_days_NDVI",
        start_date="2023-05-01",
        end_date="2023-08-31",
        aoi_feature_collection={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"city_id": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]],
                    },
                }
            ],
        },
    )

    with pytest.raises(AppEEARSRequestError) as exc_info:
        client.submit_area_task(payload)

    err = exc_info.value
    msg = str(err)
    assert err.status_code == 400
    assert "status=400" in msg
    assert "[bad_payload]" in msg
    assert "city_id=1" in msg
    assert "product=MOD13A1.061" in msg
    assert "Invalid layer selection" in msg
    assert err.response_text == "Invalid layer selection"


def test_submit_task_403_with_static_token_is_classified_as_stale_or_invalid_token():
    response = _FakeResponse(
        status_code=403,
        json_payload={"message": "You don't have the permission to access the requested resource."},
    )
    client = AppEEARSClient(
        auth=AppEEARSAuthConfig(token="stale-token", username=None, password=None),
        session=_FakeSession(response),
    )

    payload = build_area_task_payload(
        task_name="ndvi_phoenix_2023",
        product="MOD13A1.061",
        layer="500m_16_days_NDVI",
        start_date="2023-05-01",
        end_date="2023-08-31",
        aoi_feature_collection={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"city_id": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]],
                    },
                }
            ],
        },
    )

    with pytest.raises(AppEEARSRequestError) as exc_info:
        client.submit_area_task(payload)

    msg = str(exc_info.value)
    assert "[stale_or_invalid_token]" in msg
    assert "auth_mode=APPEEARS_API_TOKEN" in msg
    assert "Unset APPEEARS_API_TOKEN" in msg


def test_submit_task_timeout_recovers_by_matching_existing_task_name():
    session = _SequenceSession(
        [
            requests.Timeout("timed out"),
            _FakeResponse(
                status_code=200,
                json_payload=[{"task_name": "ndvi_phoenix_2023", "task_id": "task-123"}],
            ),
        ]
    )
    client = AppEEARSClient(
        auth=AppEEARSAuthConfig(token="test-token", username=None, password=None),
        session=session,
    )
    payload = build_area_task_payload(
        task_name="ndvi_phoenix_2023",
        product="MOD13A1.061",
        layer="500m_16_days_NDVI",
        start_date="2023-05-01",
        end_date="2023-08-31",
        aoi_feature_collection={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"city_id": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]],
                    },
                }
            ],
        },
    )

    result = client.submit_area_task(payload)

    assert result.task_id == "task-123"
    assert session.calls[0]["url"].endswith("/task")
    assert session.calls[1]["url"].endswith("/task")


def test_submit_task_timeout_without_matching_task_raises_recoverable_error():
    session = _SequenceSession(
        [
            requests.Timeout("timed out"),
            _FakeResponse(status_code=200, json_payload=[]),
        ]
    )
    client = AppEEARSClient(
        auth=AppEEARSAuthConfig(token="test-token", username=None, password=None),
        session=session,
    )
    payload = build_area_task_payload(
        task_name="ndvi_phoenix_2023",
        product="MOD13A1.061",
        layer="500m_16_days_NDVI",
        start_date="2023-05-01",
        end_date="2023-08-31",
        aoi_feature_collection={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"city_id": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]],
                    },
                }
            ],
        },
    )

    with pytest.raises(AppEEARSRequestError) as exc_info:
        client.submit_area_task(payload)

    err = exc_info.value
    assert err.reason == "request_timeout"
    assert err.recoverable is True
    assert "submission state remains unknown" in str(err)
