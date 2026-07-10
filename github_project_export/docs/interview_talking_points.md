# Interview Talking Points

## Why RTO Only

The project stays focused on one semiconductor module so the SPC logic is clear and auditable.

## Why Baseline-Only Limits

Monitoring excursions must not move the control limits. Limits are frozen from baseline rows for each tool/chamber/recipe/metric stream.

## Why No Shared Fleet Limits

Fleet charts compare streams visually. Each stream keeps its own precomputed UCL, CL, and LCL.

## Why Deterministic Rules

The goal is deterministic SPC and threshold logic, not black-box anomaly detection.

## Why No External API

The dashboard must run locally without API keys.
