from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.schema_validation import validate_all_data_files, validation_passed


def main() -> int:
    results = validate_all_data_files(ROOT_DIR / "data")
    for result in results:
        status = "PASS" if result.valid else "FAIL"
        detail = "; ".join(result.errors) if result.errors else f"{result.row_count} rows"
        print(f"{status} {result.filename}: {detail}")
    return 0 if validation_passed(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
