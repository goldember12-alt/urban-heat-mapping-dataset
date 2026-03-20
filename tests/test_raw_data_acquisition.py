import re
import zipfile
from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, box

import src.raw_data_acquisition as raw_data_acquisition
from src.city_processing import city_output_paths
from src.load_cities import load_cities
from src.raw_data_acquisition import (
    _dem_tile_key,
    _select_latest_products_by_key,
    _tnm_products,
    _acquire_hydro_for_city,
    _zip_member_name,
    collect_nhdplus_water_features,
    run_raw_data_acquisition,
)
from src.support_layers import expected_support_layer_raw_paths


def test_select_latest_products_by_key_prefers_newest_dem_tile_version():
    items = [
        {
            "title": "USGS 1 Arc Second n34w112 20210301",
            "downloadURL": "https://example.com/historical/n34w112/USGS_1_n34w112_20210301.tif",
            "publicationDate": "2021-03-01",
            "lastUpdated": "2021-03-02T00:00:00",
        },
        {
            "title": "USGS 1 Arc Second n34w112 20240402",
            "downloadURL": "https://example.com/historical/n34w112/USGS_1_n34w112_20240402.tif",
            "publicationDate": "2024-04-02",
            "lastUpdated": "2024-04-03T00:00:00",
        },
        {
            "title": "USGS 1 Arc Second n34w113 20241016",
            "downloadURL": "https://example.com/historical/n34w113/USGS_1_n34w113_20241016.tif",
            "publicationDate": "2024-10-16",
            "lastUpdated": "2024-10-17T00:00:00",
        },
    ]

    selected = _select_latest_products_by_key(items, key_parser=_dem_tile_key)

    assert len(selected) == 2
    assert selected[0]["downloadURL"].endswith("USGS_1_n34w112_20240402.tif")
    assert selected[1]["downloadURL"].endswith("USGS_1_n34w113_20241016.tif")


def test_zip_member_name_finds_target_2021_nlcd_asset(tmp_path: Path):
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("nested/Annual_NLCD_LndCov_2020_CU_C1V1.tif", b"2020")
        archive.writestr("nested/Annual_NLCD_LndCov_2021_CU_C1V1.tif", b"2021")

    member = _zip_member_name(zip_path, pattern=re.compile(r"Annual_NLCD_LndCov_2021_.*\.tif$", re.IGNORECASE))

    assert member == "nested/Annual_NLCD_LndCov_2021_CU_C1V1.tif"


def test_collect_nhdplus_water_features_reads_expected_layers(tmp_path: Path):
    package_path = tmp_path / "nhdplus_sample.gpkg"
    waterbody = gpd.GeoDataFrame({"FType": [390]}, geometry=[box(0, 0, 5, 5)], crs="EPSG:3857")
    flowline = gpd.GeoDataFrame({"FType": [460]}, geometry=[LineString([(0, 10), (10, 10)])], crs="EPSG:3857")
    ignored = gpd.GeoDataFrame({"name": ["ignore"]}, geometry=[box(20, 20, 30, 30)], crs="EPSG:3857")

    waterbody.to_file(package_path, layer="NHDWaterbody", driver="GPKG")
    flowline.to_file(package_path, layer="NHDFlowline", driver="GPKG")
    ignored.to_file(package_path, layer="WBDHU4", driver="GPKG")

    study_area = gpd.GeoDataFrame({"city_id": [1]}, geometry=[box(-1, -1, 12, 12)], crs="EPSG:3857")
    water = collect_nhdplus_water_features(package_path=package_path, study_area_gdf=study_area)

    assert sorted(water["source_layer"].unique().tolist()) == ["NHDFlowline", "NHDWaterbody"]
    assert len(water) == 2


def test_collect_nhdplus_water_features_uses_bbox_when_reading_layers(tmp_path: Path, monkeypatch):
    package_path = tmp_path / "nhdplus_sample.gpkg"
    waterbody = gpd.GeoDataFrame({"FType": [390]}, geometry=[box(0, 0, 5, 5)], crs="EPSG:3857")
    flowline = gpd.GeoDataFrame({"FType": [460]}, geometry=[LineString([(0, 10), (10, 10)])], crs="EPSG:3857")

    waterbody.to_file(package_path, layer="NHDWaterbody", driver="GPKG")
    flowline.to_file(package_path, layer="NHDFlowline", driver="GPKG")

    study_area = gpd.GeoDataFrame({"city_id": [1]}, geometry=[box(-1, -1, 12, 12)], crs="EPSG:3857")

    recorded_kwargs: list[dict[str, object]] = []
    real_read_file = gpd.read_file

    def _tracking_read_file(*args, **kwargs):
        if Path(args[0]) == package_path:
            recorded_kwargs.append(dict(kwargs))
        return real_read_file(*args, **kwargs)

    monkeypatch.setattr(raw_data_acquisition.gpd, "read_file", _tracking_read_file)

    water = collect_nhdplus_water_features(package_path=package_path, study_area_gdf=study_area)

    assert len(water) == 2
    assert len(recorded_kwargs) == 2
    assert all("bbox" in kwargs for kwargs in recorded_kwargs)
    assert all(len(tuple(kwargs["bbox"])) == 4 for kwargs in recorded_kwargs)


class _FakeTNMResponse:
    def __init__(self, status_code: int, payload: dict[str, object]):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)
        self.headers: dict[str, str] = {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeTNMSession:
    def __init__(self, responses: list[_FakeTNMResponse]):
        self._responses = list(responses)
        self.calls: list[tuple[str, str, object]] = []

    def request(self, method, url, params=None, headers=None, stream=False, timeout=None):
        self.calls.append((method, url, params))
        return self._responses.pop(0)


class _StreamingResponse:
    def __init__(self, status_code: int, chunks: list[object], headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._chunks = list(chunks)
        self.headers = headers or {}
        self.text = ""

    def iter_content(self, chunk_size=1024):
        for chunk in self._chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _StreamingSession:
    def __init__(self, responses: list[_StreamingResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method, url, params=None, headers=None, stream=False, timeout=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "stream": stream})
        return self._responses.pop(0)


def test_tnm_products_retries_transient_gateway_timeout(monkeypatch):
    session = _FakeTNMSession(
        [
            _FakeTNMResponse(504, {"error": "Gateway Timeout"}),
            _FakeTNMResponse(200, {"items": [{"downloadURL": "https://example.com/final.tif"}]}),
        ]
    )
    monkeypatch.setattr(raw_data_acquisition.time, "sleep", lambda *_args, **_kwargs: None)

    items = _tnm_products(
        session=session,
        dataset_name="dataset",
        bbox_wgs84=(-1.0, -1.0, 1.0, 1.0),
    )

    assert len(items) == 1
    assert items[0]["downloadURL"] == "https://example.com/final.tif"
    assert len(session.calls) == 2


def test_tnm_products_retries_invalid_json_payload(monkeypatch):
    session = _FakeTNMSession(
        [
            _FakeTNMResponse(200, requests.JSONDecodeError("bad json", "{bad", 1)),
            _FakeTNMResponse(200, {"items": [{"downloadURL": "https://example.com/final.tif"}]}),
        ]
    )
    monkeypatch.setattr(raw_data_acquisition.time, "sleep", lambda *_args, **_kwargs: None)

    items = _tnm_products(
        session=session,
        dataset_name="dataset",
        bbox_wgs84=(-1.0, -1.0, 1.0, 1.0),
    )

    assert len(items) == 1
    assert len(session.calls) == 2


def test_download_file_resumes_partial_after_chunked_transfer_failure(tmp_path: Path, monkeypatch):
    destination = tmp_path / "NHDPLUS_H_1303_HU4_GPKG.zip"
    session = _StreamingSession(
        [
                _StreamingResponse(
                    200,
                    chunks=[b"abcde", requests.exceptions.ChunkedEncodingError("stream interrupted")],
                    headers={"Content-Length": "10"},
                ),
            _StreamingResponse(
                206,
                chunks=[b"fghij"],
                headers={"Content-Length": "5", "Content-Range": "bytes 5-9/10"},
            ),
        ]
    )
    monkeypatch.setattr(raw_data_acquisition.time, "sleep", lambda *_args, **_kwargs: None)

    result = raw_data_acquisition._download_file(session=session, url="https://example.com/file.zip", destination=destination)

    assert result == destination
    assert destination.read_bytes() == b"abcdefghij"
    assert session.calls[1]["headers"]["Range"] == "bytes=5-"


def test_acquire_hydro_for_city_requeries_dead_package_url(tmp_path: Path, monkeypatch):
    study_area = gpd.GeoDataFrame({"city_id": [3]}, geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")
    output_path = tmp_path / "las_vegas_hydro.gpkg"
    cache_dir = tmp_path / "cache"
    session = requests.Session()
    query_calls: list[int] = []

    initial_items = [
        {
            "title": "HU) 4 - 1606",
            "format": "GeoPackage",
            "downloadURL": "https://example.com/NHDPLUS_H_1606_old.zip",
            "publicationDate": "2022-04-18",
            "lastUpdated": "2022-04-18T00:00:00",
        }
    ]
    refreshed_items = [
        {
            "title": "HU) 4 - 1606",
            "format": "GeoPackage",
            "downloadURL": "https://example.com/NHDPLUS_H_1606_new.zip",
            "publicationDate": "2025-01-01",
            "lastUpdated": "2025-01-01T00:00:00",
        }
    ]

    def fake_tnm_products(**kwargs):
        query_calls.append(1)
        return initial_items if len(query_calls) == 1 else refreshed_items

    def fake_download_file(*, url, destination, **kwargs):
        if url.endswith("_old.zip"):
            raise requests.HTTPError("404", response=SimpleNamespace(status_code=404))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("zip")
        return destination

    def fake_extract_zip_member(zip_path: Path, member_name: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("gpkg")
        return destination

    def fake_collect(package_path: Path, study_area_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame({"source_layer": ["NHDWaterbody"]}, geometry=[box(0, 0, 1, 1)], crs=study_area_gdf.crs)

    monkeypatch.setattr(raw_data_acquisition, "_study_area_bbox_wgs84", lambda *_args, **_kwargs: (-1.0, -1.0, 1.0, 1.0))
    monkeypatch.setattr(raw_data_acquisition, "_study_area_geometry", lambda *_args, **_kwargs: (study_area, study_area.geometry.iloc[0]))
    monkeypatch.setattr(raw_data_acquisition, "_tnm_products", fake_tnm_products)
    monkeypatch.setattr(raw_data_acquisition, "_download_file", fake_download_file)
    monkeypatch.setattr(raw_data_acquisition, "_hydro_geopackage_zip_member", lambda *_args, **_kwargs: "package.gpkg")
    monkeypatch.setattr(raw_data_acquisition, "_extract_zip_member", fake_extract_zip_member)
    monkeypatch.setattr(raw_data_acquisition, "collect_nhdplus_water_features", fake_collect)
    monkeypatch.setattr(raw_data_acquisition, "_write_vector_output", lambda gdf, output_path, layer="water": output_path)

    result = _acquire_hydro_for_city(
        study_area_path=tmp_path / "study_area.gpkg",
        output_path=output_path,
        session=session,
        cache_dir=cache_dir,
    )

    assert query_calls == [1, 1]
    assert result["source_urls"] == ["https://example.com/NHDPLUS_H_1606_new.zip"]
    assert result["n_source_files"] == 1


def test_run_raw_data_acquisition_skips_existing_outputs_without_force(tmp_path: Path):
    city = load_cities().iloc[0]
    study_area_path, _ = city_output_paths(
        city,
        resolution=30,
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
    )
    study_area_path.parent.mkdir(parents=True, exist_ok=True)
    study_area_path.write_text("placeholder")

    expected_raw = expected_support_layer_raw_paths(
        city,
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
    )
    for path in [
        expected_raw.dem_raster,
        expected_raw.nlcd_land_cover_raster,
        expected_raw.nlcd_impervious_raster,
        expected_raw.hydro_vector,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ready")

    result = run_raw_data_acquisition(
        dataset="all",
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        dem_cache_dir=tmp_path / "cache" / "dem",
        nlcd_cache_dir=tmp_path / "cache" / "nlcd",
        hydro_cache_dir=tmp_path / "cache" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
    )

    assert len(result.summary) == 3
    assert set(result.summary["dataset"].tolist()) == {"dem", "nlcd", "hydro"}
    assert set(result.summary["status"].tolist()) == {"skipped_existing"}
    assert result.summary_json_path.exists()
    assert result.summary_csv_path.exists()


def test_run_raw_data_acquisition_records_structured_failure_metadata(tmp_path: Path, monkeypatch):
    city = load_cities().iloc[0]
    study_area_path, _ = city_output_paths(
        city,
        resolution=30,
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
    )
    study_area_path.parent.mkdir(parents=True, exist_ok=True)
    study_area_path.write_text("placeholder")

    monkeypatch.setattr(
        raw_data_acquisition,
        "audit_support_layer_readiness",
        lambda **kwargs: SimpleNamespace(
            summary=pd.DataFrame(
                [
                    {
                        "city_id": int(city["city_id"]),
                        "dem_source_available": False,
                        "nlcd_land_cover_source_available": False,
                        "nlcd_impervious_source_available": False,
                        "hydro_source_available": False,
                    }
                ]
            )
        ),
    )
    monkeypatch.setattr(
        raw_data_acquisition,
        "_acquire_dem_for_city",
        lambda **kwargs: (_ for _ in ()).throw(requests.exceptions.ChunkedEncodingError("stream interrupted")),
    )

    result = run_raw_data_acquisition(
        dataset="dem",
        city_ids=[int(city["city_id"])],
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        dem_cache_dir=tmp_path / "cache" / "dem",
        nlcd_cache_dir=tmp_path / "cache" / "nlcd",
        hydro_cache_dir=tmp_path / "cache" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
    )

    row = result.summary.iloc[0]
    assert row["status"] == "failed"
    assert row["failure_reason"] == "download_stream_interrupted"
    assert row["failure_category"] == "network_download"
    assert bool(row["recoverable"]) is True
