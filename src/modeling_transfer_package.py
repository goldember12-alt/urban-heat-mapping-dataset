from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from joblib import dump

from src.config import MODELING_FINAL_TRAIN_OUTPUTS
from src.modeling_config import (
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_FINAL_DATASET_PATH,
    get_feature_type_map,
)
from src.modeling_data import (
    drop_missing_target_rows,
    load_city_outer_folds,
    load_modeling_rows,
    load_sampled_modeling_rows_with_diagnostics,
    validate_model_feature_columns,
    write_feature_contract,
)
from src.modeling_prep import get_final_dataset_columns
from src.modeling_reporting import DEFAULT_RF_FRONTIER_RUN_DIR
from src.modeling_runner import build_logistic_saga_pipeline, build_random_forest_pipeline

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HyperparameterSelectionResult:
    selected_params: dict[str, object]
    summary_df: pd.DataFrame
    selected_signature: str


@dataclass(frozen=True)
class TransferPackageResult:
    output_dir: Path
    model_artifact_path: Path
    metadata_path: Path
    feature_contract_path: Path
    preprocessing_manifest_path: Path
    hyperparameter_summary_path: Path
    selected_hyperparameters_path: Path
    training_city_summary_path: Path
    training_sample_diagnostics_path: Path | None


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(_require_file(path).read_text(encoding="utf-8"))


def build_transfer_package_dirname(
    *,
    model_name: str,
    tuning_preset: str,
    sample_rows_per_city: int | None,
) -> str:
    """Return a deterministic final-train package directory name."""
    sample_scope = "fullrows" if sample_rows_per_city is None else f"s{int(sample_rows_per_city)}"
    return f"{model_name}_{tuning_preset}_{sample_scope}_all_cities_transfer_package"


def select_consensus_hyperparameters(best_params_df: pd.DataFrame) -> HyperparameterSelectionResult:
    """Choose one deterministic hyperparameter set from per-fold winners."""
    required_columns = {"best_params_json", "best_inner_cv_average_precision"}
    missing_columns = sorted(required_columns - set(best_params_df.columns))
    if missing_columns:
        raise ValueError(
            "Best-parameter table is missing required columns: " + ", ".join(missing_columns)
        )

    working = best_params_df.copy()
    working["best_params_signature"] = working["best_params_json"].map(
        lambda raw_value: json.dumps(json.loads(str(raw_value)), sort_keys=True)
    )
    summary_df = (
        working.groupby("best_params_signature", dropna=False)
        .agg(
            fold_count=("best_params_signature", "count"),
            mean_best_inner_cv_average_precision=("best_inner_cv_average_precision", "mean"),
            outer_fold_min=("outer_fold", "min"),
        )
        .reset_index()
        .sort_values(
            [
                "fold_count",
                "mean_best_inner_cv_average_precision",
                "best_params_signature",
            ],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )
    selected_signature = str(summary_df.loc[0, "best_params_signature"])
    selected_params = json.loads(selected_signature)
    return HyperparameterSelectionResult(
        selected_params=selected_params,
        summary_df=summary_df,
        selected_signature=selected_signature,
    )


def _resolve_pipeline_builder(model_name: str):
    normalized_model_name = model_name.strip().lower()
    if normalized_model_name == "random_forest":
        return build_random_forest_pipeline
    if normalized_model_name == "logistic_saga":
        return build_logistic_saga_pipeline
    raise ValueError(f"Unsupported final-train transfer package model: {model_name}")


def _build_preprocessing_manifest(
    *,
    model_name: str,
    feature_columns: list[str],
    pipeline_builder_kwargs: dict[str, object],
) -> dict[str, object]:
    feature_type_map = get_feature_type_map(feature_columns)
    numeric_columns = [column for column, feature_type in feature_type_map.items() if feature_type == "numeric"]
    categorical_columns = [column for column, feature_type in feature_type_map.items() if feature_type == "categorical"]
    if model_name == "random_forest":
        preprocessing_steps = {
            "numeric": ["coerce_numeric", "median_imputer"],
            "categorical": ["coerce_categorical", "most_frequent_imputer", "ordinal_encoder_unknown=-1"],
        }
    else:
        preprocessing_steps = {
            "numeric": ["coerce_numeric", "median_imputer", "standard_scaler"],
            "categorical": ["coerce_categorical", "most_frequent_imputer", "one_hot_encoder_ignore_unknown"],
        }
    return {
        "model_name": model_name,
        "selected_feature_columns": feature_columns,
        "feature_type_map": feature_type_map,
        "numeric_feature_columns": numeric_columns,
        "categorical_feature_columns": categorical_columns,
        "preprocessing_steps": preprocessing_steps,
        "pipeline_builder_kwargs": pipeline_builder_kwargs,
    }


def _summarize_training_rows(training_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        training_df.groupby(["city_id", "city_name", "climate_group"], dropna=False)
        .agg(
            row_count=("cell_id", "count"),
            hotspot_positive_count=("hotspot_10pct", "sum"),
        )
        .reset_index()
        .sort_values(["city_id"])
        .reset_index(drop=True)
    )
    summary["hotspot_prevalence"] = summary["hotspot_positive_count"] / summary["row_count"]
    return summary


def build_final_transfer_package(
    *,
    reference_run_dir: Path = DEFAULT_RF_FRONTIER_RUN_DIR,
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    output_dir: Path | None = None,
    sample_rows_per_city: int | None = None,
    model_n_jobs: int | None = None,
) -> TransferPackageResult:
    """Fit the retained benchmark-selected model on all cities for transfer-oriented packaging."""
    resolved_reference_run_dir = reference_run_dir.resolve()
    metadata = _load_json(resolved_reference_run_dir / "run_metadata.json")
    best_params_df = pd.read_csv(_require_file(resolved_reference_run_dir / "best_params_by_fold.csv"))
    feature_contract = _load_json(resolved_reference_run_dir / "feature_contract.json")

    model_name = str(metadata["model_name"])
    tuning_preset = str(metadata["tuning_preset"])
    selected_feature_columns = list(feature_contract.get("selected_feature_columns", DEFAULT_FEATURE_COLUMNS))
    validate_model_feature_columns(
        feature_columns=selected_feature_columns,
        available_columns=get_final_dataset_columns(dataset_path=dataset_path),
    )

    reference_sample_rows = metadata.get("sample_rows_per_city")
    resolved_sample_rows_per_city = None if sample_rows_per_city == 0 else sample_rows_per_city
    if sample_rows_per_city is None:
        resolved_sample_rows_per_city = None if reference_sample_rows is None else int(reference_sample_rows)

    resolved_output_dir = (
        output_dir
        if output_dir is not None
        else MODELING_FINAL_TRAIN_OUTPUTS
        / build_transfer_package_dirname(
            model_name=model_name,
            tuning_preset=tuning_preset,
            sample_rows_per_city=resolved_sample_rows_per_city,
        )
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    selection_result = select_consensus_hyperparameters(best_params_df)
    hyperparameter_summary_path = resolved_output_dir / "hyperparameter_selection_summary.csv"
    selection_result.summary_df.to_csv(hyperparameter_summary_path, index=False)
    selected_hyperparameters_path = resolved_output_dir / "selected_hyperparameters.json"
    selected_hyperparameters_path.write_text(
        json.dumps(selection_result.selected_params, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    resolved_folds_path = folds_path if folds_path is not None else metadata.get("folds_path")
    fold_table = load_city_outer_folds(None if resolved_folds_path is None else Path(str(resolved_folds_path)))
    city_ids = fold_table["city_id"].astype(int).tolist()

    if resolved_sample_rows_per_city is None:
        training_df = drop_missing_target_rows(
            load_modeling_rows(
                dataset_path=dataset_path,
                feature_columns=selected_feature_columns,
                city_ids=city_ids,
            )
        )
        training_sample_diagnostics_df = None
    else:
        sampled_df, training_sample_diagnostics_df = load_sampled_modeling_rows_with_diagnostics(
            dataset_path=dataset_path,
            feature_columns=selected_feature_columns,
            city_ids=city_ids,
            sample_rows_per_city=int(resolved_sample_rows_per_city),
            random_state=int(metadata.get("random_state", 42)),
        )
        training_df = drop_missing_target_rows(sampled_df)

    training_city_summary_df = _summarize_training_rows(training_df)
    training_city_summary_path = resolved_output_dir / "training_city_summary.csv"
    training_city_summary_df.to_csv(training_city_summary_path, index=False)

    training_sample_diagnostics_path: Path | None = None
    if training_sample_diagnostics_df is not None:
        training_sample_diagnostics_path = resolved_output_dir / "training_sample_diagnostics.csv"
        training_sample_diagnostics_df.to_csv(training_sample_diagnostics_path, index=False)

    pipeline_builder = _resolve_pipeline_builder(model_name)
    pipeline_builder_kwargs = dict(metadata.get("pipeline_builder_kwargs", {}))
    resolved_model_n_jobs = model_n_jobs if model_n_jobs is not None else metadata.get("model_n_jobs")
    pipeline = pipeline_builder(
        feature_columns=selected_feature_columns,
        random_state=int(metadata.get("random_state", 42)),
        n_jobs=None if resolved_model_n_jobs is None else int(resolved_model_n_jobs),
        memory=None,
        **pipeline_builder_kwargs,
    )
    pipeline.set_params(**selection_result.selected_params)
    pipeline.fit(training_df[selected_feature_columns], training_df["hotspot_10pct"].astype("int8"))

    model_artifact_path = resolved_output_dir / "model.joblib"
    dump(pipeline, model_artifact_path)

    feature_contract_path = resolved_output_dir / "feature_contract.json"
    write_feature_contract(feature_contract_path, feature_columns=selected_feature_columns)

    preprocessing_manifest_path = resolved_output_dir / "preprocessing_manifest.json"
    preprocessing_manifest_path.write_text(
        json.dumps(
            _build_preprocessing_manifest(
                model_name=model_name,
                feature_columns=selected_feature_columns,
                pipeline_builder_kwargs=pipeline_builder_kwargs,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    metadata_path = resolved_output_dir / "transfer_package_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "artifact_kind": "final_train_transfer_package",
                "intended_use": "Apply the retained six-feature hotspot model to new-city transfer workflows after benchmark selection is complete.",
                "benchmark_framing_note": "This package supports the canonical cross-city city-held-out benchmark story and is not itself a new benchmark result.",
                "source_reference_run_dir": str(resolved_reference_run_dir),
                "source_reference_model_name": model_name,
                "source_reference_tuning_preset": tuning_preset,
                "reference_sample_rows_per_city": reference_sample_rows,
                "training_dataset_path": str(dataset_path),
                "training_folds_path": None if resolved_folds_path is None else str(resolved_folds_path),
                "training_city_count": int(training_city_summary_df["city_id"].nunique()),
                "training_row_count": int(len(training_df)),
                "training_positive_count": int(training_df["hotspot_10pct"].sum()),
                "training_hotspot_prevalence": float(training_df["hotspot_10pct"].mean()),
                "sample_rows_per_city": resolved_sample_rows_per_city,
                "selected_feature_columns": selected_feature_columns,
                "selected_hyperparameters": selection_result.selected_params,
                "hyperparameter_selection_rule": {
                    "primary": "most frequent best_params_json across outer folds",
                    "secondary": "highest mean best_inner_cv_average_precision",
                    "tertiary": "lexicographic best_params_signature",
                    "selected_signature": selection_result.selected_signature,
                },
                "random_state": int(metadata.get("random_state", 42)),
                "model_n_jobs": resolved_model_n_jobs,
                "source_reporting_note": (
                    "The current retained benchmark report treats the RF frontier checkpoint as the bounded nonlinear reference."
                    if model_name == "random_forest"
                    else "This package reuses a retained logistic checkpoint without changing the canonical benchmark framing."
                ),
                "output_files": {
                    "model_artifact": str(model_artifact_path),
                    "feature_contract": str(feature_contract_path),
                    "preprocessing_manifest": str(preprocessing_manifest_path),
                    "selected_hyperparameters": str(selected_hyperparameters_path),
                    "hyperparameter_selection_summary": str(hyperparameter_summary_path),
                    "training_city_summary": str(training_city_summary_path),
                    "training_sample_diagnostics": (
                        None if training_sample_diagnostics_path is None else str(training_sample_diagnostics_path)
                    ),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    LOGGER.info("Wrote final-train transfer package under %s", resolved_output_dir)
    return TransferPackageResult(
        output_dir=resolved_output_dir,
        model_artifact_path=model_artifact_path,
        metadata_path=metadata_path,
        feature_contract_path=feature_contract_path,
        preprocessing_manifest_path=preprocessing_manifest_path,
        hyperparameter_summary_path=hyperparameter_summary_path,
        selected_hyperparameters_path=selected_hyperparameters_path,
        training_city_summary_path=training_city_summary_path,
        training_sample_diagnostics_path=training_sample_diagnostics_path,
    )
