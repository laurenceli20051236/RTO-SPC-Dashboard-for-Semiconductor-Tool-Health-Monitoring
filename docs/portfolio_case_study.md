# Portfolio Case Study

## Problem

Weekly RTO monitor review becomes difficult when chamber-level thickness and particle streams are spread across tools, recipes, and metrics. Reviewers need fleet context without destroying the statistical identity of each individual stream.

## Engineering Response

I built a deterministic Python pipeline and Streamlit dashboard that:

- generates public-safe synthetic RTO monitor data;
- aligns synthetic tools around common golden centers while preserving chamber and recipe offsets;
- freezes thickness control limits from baseline rows only;
- applies limits separately to every tool/chamber/recipe/metric stream;
- uses threshold and repeated-event logic for particle monitoring;
- persists every warning or OOC result to an auditable event table;
- presents fleet overlays, tool health prioritization, drilldown, and CSV export.

## Key Design Decisions

### Fleet View Without Shared Limits

Fleet charts are a visual comparison layer. Each point retains the UCL, CL, LCL, threshold, and event status calculated for its own stream.

### Deterministic Before Predictive

The project focuses on explainable SPC and threshold logic. It deliberately excludes black-box anomaly detection, automated diagnosis, and external model APIs.

### Data Contracts Before UI

The dashboard reads generated CSV outputs through schema validation. Rule execution and event persistence happen before rendering, which keeps presentation logic separate from engineering decisions.

## Capability Evidence

| Capability | Evidence |
| --- | --- |
| Semiconductor process understanding | RTO thickness and particle monitor definitions, chamber-level review, and engineering-safe scope boundaries |
| Statistical process control | Baseline-only per-stream limits, warning/OOC rules, and one-sided variation handling |
| Python engineering | Modular package design, deterministic generators, tests, and release scripts |
| Data engineering | Stable schemas, validation, persisted outputs, hashed synthetic identifiers, and reproducible seeds |
| Product thinking | Fleet-to-stream review path, concise 14-week overlays, health prioritization, and exportable events |
| Delivery discipline | GitHub Actions, deployment instructions, public-safety documentation, and release QA |

## Limitations

The data and thresholds are synthetic. The project is not a production decision system and does not determine root cause, ingest fab data, or claim production validation.
