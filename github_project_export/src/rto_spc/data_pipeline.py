from __future__ import annotations

from pathlib import Path

from rto_spc.config import RANDOM_SEED
from rto_spc.control_limits import apply_baseline_thickness_limits
from rto_spc.data_generator import generate_monitor_measurements
from rto_spc.data_loader import DATA_DIR
from rto_spc.excursion_scoring import build_excursion_events
from rto_spc.particle_rules import apply_particle_threshold_rules
from rto_spc.thickness_monitor_rules import apply_thickness_monitor_rules


def generate_all_sample_data(output_dir: Path | None = None, seed: int = RANDOM_SEED) -> dict[str, Path]:
    """Generate synthetic RTO dashboard CSV outputs."""
    data_dir = output_dir or DATA_DIR
    data_dir.mkdir(exist_ok=True)

    measurements = generate_monitor_measurements(seed=seed)
    spc_results = apply_baseline_thickness_limits(measurements)
    spc_results = apply_thickness_monitor_rules(spc_results)
    spc_results = apply_particle_threshold_rules(spc_results)
    excursion_events = build_excursion_events(spc_results)

    outputs = {
        "monitor_measurements": data_dir / "monitor_measurements.csv",
        "spc_results": data_dir / "spc_results.csv",
        "excursion_events": data_dir / "excursion_events.csv",
    }

    measurements.to_csv(outputs["monitor_measurements"], index=False)
    spc_results.to_csv(outputs["spc_results"], index=False)
    excursion_events.to_csv(outputs["excursion_events"], index=False)

    return outputs
