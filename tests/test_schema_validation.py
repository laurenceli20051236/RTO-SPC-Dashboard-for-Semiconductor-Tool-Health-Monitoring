from __future__ import annotations

from pathlib import Path

import pandas as pd

from rto_spc.schema_validation import DATA_FILE_SCHEMAS, validate_all_data_files, validate_dataframe_schema, validation_passed


def test_validate_dataframe_schema_passes_required_columns() -> None:
    schema = DATA_FILE_SCHEMAS[0]
    row = {column: "synthetic" for column in schema.required_columns}
    row.update(
        {
            "phase": "baseline",
            "monitor_type": "Thickness",
            "tool_id": "RTO_A01",
            "chamber_id": "CH1",
            "recipe_group": "RTO_BASELINE",
            "metric_name": "thickness_xbar",
        }
    )
    result = validate_dataframe_schema(pd.DataFrame([row]), schema)
    assert result.valid


def test_validate_dataframe_schema_catches_missing_columns() -> None:
    schema = DATA_FILE_SCHEMAS[0]
    result = validate_dataframe_schema(pd.DataFrame([{"phase": "baseline"}]), schema)
    assert not result.valid
    assert any("missing columns" in error for error in result.errors)


def test_validate_dataframe_schema_catches_invalid_allowed_values() -> None:
    schema = DATA_FILE_SCHEMAS[0]
    row = {column: "synthetic" for column in schema.required_columns}
    row.update(
        {
            "phase": "production",
            "monitor_type": "Thickness",
            "tool_id": "RTO_A01",
            "chamber_id": "CH1",
            "recipe_group": "RTO_BASELINE",
            "metric_name": "thickness_xbar",
        }
    )
    result = validate_dataframe_schema(pd.DataFrame([row]), schema)
    assert not result.valid
    assert any("phase has invalid values" in error for error in result.errors)


def test_validate_all_data_files_passes_generated_data() -> None:
    results = validate_all_data_files(Path(__file__).resolve().parents[1] / "data")
    assert validation_passed(results)
