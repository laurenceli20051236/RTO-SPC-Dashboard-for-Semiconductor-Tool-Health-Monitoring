from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.data_pipeline import generate_all_sample_data
from rto_spc.config import RANDOM_SEED


def main() -> None:
    outputs = generate_all_sample_data(output_dir=ROOT_DIR / "data", seed=RANDOM_SEED)
    for path in outputs.values():
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
