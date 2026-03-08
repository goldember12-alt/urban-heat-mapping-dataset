import pytest

from src.appeears_client import AppEEARSAuthConfig, AppEEARSClient, AppEEARSRequestError, build_area_task_payload


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
    assert "city_id=1" in msg
    assert "product=MOD13A1.061" in msg
    assert "Invalid layer selection" in msg
    assert err.response_text == "Invalid layer selection"
