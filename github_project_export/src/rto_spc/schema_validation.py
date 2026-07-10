from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from rto_spc.data_loader import (
    DATA_DIR,
    EXCURSION_EVENT_COLUMNS,
    MONITOR_MEASUREMENT_COLUMNS,
    SPC_RESULT_COLUMNS,
)
from rto_spc.config import PARTICLE_METRICS, THICKNESS_METRICS, TOOLS, CHAMBERS, RECIPE_GROUPS


@dataclass(frozen=True)
class FileSchema:
    filename: str
    required_columns: list[str]
    allowed_values: dict[str, set[str]]


@dataclass(frozen=True)
class ValidationResult:
    filename: str
    valid: bool
    errors: list[str]
    row_count: int


DATA_FILE_SCHEMAS = [
    FileSchema(
        "monitor_measurements.csv",
        MONITOR_MEASUREMENT_COLUMNS,
        {
            "phase": {"baseline", "monitoring"},
            "monitor_type": {"Thickness", "Particle"},
            "tool_id": set(TOOLS),
            "chamber_id": set(CHAMBERS),
            "recipe_group": set(RECIPE_GROUPS),
            "metric_name": set(THICKNESS_METRICS + PARTICLE_METRICS),
        },
    ),
    FileSchema("spc_results.csv", SPC_RESULT_COLUMNS, {"phase": {"baseline", "monitoring"}, "monitor_type": {"Thickness", "Particle"}}),
    FileSchema(
        "excursion_events.csv",
        EXCURSION_EVENT_COLUMNS,
        {
            "phase": {"baseline", "monitoring"},
            "status": {"Open", "Reviewed", "Closed"},
            "event_source": {
                "phase1_thickness_monitor",
                "phase1_particle_threshold",
            },
            "method_type": {"baseline_3sigma", "threshold", "repeated_event"},
        },
    ),
]


def validate_dataframe_schema(df: pd.DataFrame, schema: FileSchema) -> ValidationResult:
    errors: list[str] = []
    missing_columns = [column for column in schema.required_columns if column not in df.columns]
    if missing_columns:
        errors.append(f"missing columns: {', '.join(missing_columns)}")

    if df.empty:
        errors.append("file has zero rows")

    for column, allowed in schema.allowed_values.items():
        if column not in df.columns:
            continue
        values = set(df[column].dropna().astype(str).unique())
        invalid = sorted(values - allowed)
        if invalid:
            errors.append(f"{column} has invalid values: {', '.join(invalid)}")

    return ValidationResult(schema.filename, not errors, errors, len(df))


def validate_csv_file(data_dir: Path, schema: FileSchema) -> ValidationResult:
    path = data_dir / schema.filename
    if not path.exists():
        return ValidationResult(schema.filename, False, ["file does not exist"], 0)

    try:
        df = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - defensive path
        return ValidationResult(schema.filename, False, [f"unable to read CSV: {exc}"], 0)
    return validate_dataframe_schema(df, schema)


def validate_all_data_files(data_dir: Path | None = None) -> list[ValidationResult]:
    root = data_dir or DATA_DIR
    return [validate_csv_file(root, schema) for schema in DATA_FILE_SCHEMAS]


def validation_passed(results: list[ValidationResult]) -> bool:
    return all(result.valid for result in results)
