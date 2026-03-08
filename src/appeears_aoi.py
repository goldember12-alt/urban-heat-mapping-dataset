from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.config import APPEEARS_AOI, STUDY_AREAS

logger = logging.getLogger(__name__)

_STUDY_AREA_PATTERN = re.compile(r"^(?P<city_id>\d+)_.*_study_area\.gpkg$", re.IGNORECASE)


@dataclass(frozen=True)
class AoiExportRecord:
    city_id: int
    city_name: str
    state: str
    city_slug: str
    study_area_path: str
    aoi_path: str
    status: str
    error: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def city_slug(city_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", city_name.strip().lower()).strip("_")


def discover_study_area_files(study_areas_dir: Path = STUDY_AREAS) -> list[Path]:
    """Return sorted study-area GeoPackage files in the configured output folder."""
    if not study_areas_dir.exists():
        return []
    return sorted(path for path in study_areas_dir.glob("*_study_area.gpkg") if path.is_file())


def build_study_area_index(study_areas_dir: Path = STUDY_AREAS) -> dict[int, Path]:
    """Build {city_id: study_area_path} from discovered study-area outputs."""
    index: dict[int, Path] = {}
    for path in discover_study_area_files(study_areas_dir=study_areas_dir):
        match = _STUDY_AREA_PATTERN.match(path.name)
        if match is None:
            continue
        city_id = int(match.group("city_id"))
        index[city_id] = path
    return index


def _read_study_area_geometry(study_area_path: Path):
    study_area = gpd.read_file(study_area_path)
    if study_area.empty:
        raise ValueError(f"Study area is empty: {study_area_path}")
    if study_area.crs is None:
        raise ValueError(f"Study area has no CRS: {study_area_path}")

    geometry_series = study_area.geometry
    if hasattr(geometry_series, "union_all"):
        geometry = geometry_series.union_all()
    else:  # pragma: no cover
        geometry = geometry_series.unary_union

    if geometry is None or geometry.is_empty:
        raise ValueError(f"Study area has empty geometry: {study_area_path}")
    return study_area, geometry


def export_city_aoi(
    city: pd.Series,
    study_area_path: Path,
    aoi_dir: Path = APPEEARS_AOI,
) -> AoiExportRecord:
    """Export one AppEEARS-ready city AOI GeoJSON in EPSG:4326."""
    cid = int(city["city_id"])
    cname = str(city["city_name"])
    state = str(city["state"])
    slug = city_slug(cname)
    stem = f"{cid:02d}_{slug}_{state.lower()}"
    aoi_path = aoi_dir / f"{stem}_aoi.geojson"

    try:
        study_area, geometry = _read_study_area_geometry(study_area_path)
        aoi = gpd.GeoDataFrame(
            {
                "city_id": [cid],
                "city_name": [cname],
                "state": [state],
            },
            geometry=[geometry],
            crs=study_area.crs,
        ).to_crs(epsg=4326)

        aoi_dir.mkdir(parents=True, exist_ok=True)
        aoi.to_file(aoi_path, driver="GeoJSON")
        logger.info("Exported AppEEARS AOI for city_id=%s to %s", cid, aoi_path)
        return AoiExportRecord(
            city_id=cid,
            city_name=cname,
            state=state,
            city_slug=slug,
            study_area_path=str(study_area_path),
            aoi_path=str(aoi_path),
            status="exported",
            error="",
        )
    except Exception as exc:
        logger.exception("AOI export failed for city_id=%s", cid)
        return AoiExportRecord(
            city_id=cid,
            city_name=cname,
            state=state,
            city_slug=slug,
            study_area_path=str(study_area_path),
            aoi_path=str(aoi_path),
            status="failed",
            error=str(exc),
        )


def export_appeears_aois(
    cities: pd.DataFrame,
    study_areas_dir: Path = STUDY_AREAS,
    aoi_dir: Path = APPEEARS_AOI,
) -> pd.DataFrame:
    """Export AOIs for selected cities using discovered study-area GeoPackages."""
    index = build_study_area_index(study_areas_dir=study_areas_dir)
    rows: list[dict[str, object]] = []

    for _, city in cities.iterrows():
        cid = int(city["city_id"])
        path = index.get(cid)
        if path is None:
            rows.append(
                AoiExportRecord(
                    city_id=cid,
                    city_name=str(city["city_name"]),
                    state=str(city["state"]),
                    city_slug=city_slug(str(city["city_name"])),
                    study_area_path="",
                    aoi_path="",
                    status="blocked",
                    error="study_area_missing",
                ).to_dict()
            )
            continue

        record = export_city_aoi(city=city, study_area_path=path, aoi_dir=aoi_dir)
        rows.append(record.to_dict())

    return pd.DataFrame(rows)


def load_aoi_feature_collection(aoi_path: Path) -> dict[str, object]:
    """Load an AOI GeoJSON file as a feature collection dict for API payloads."""
    with aoi_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"AOI is not a FeatureCollection: {aoi_path}")
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError(f"AOI has no features: {aoi_path}")
    return payload
