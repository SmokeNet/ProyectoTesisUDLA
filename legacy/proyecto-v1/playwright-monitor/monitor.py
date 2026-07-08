"""Adaptador CLI compatible para el motor profesional de observabilidad."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observability.config import Settings  # noqa: E402
from observability.logging_config import configure_logging  # noqa: E402
from observability.orchestrator import ObservationOrchestrator  # noqa: E402


def main() -> int:
    configure_logging()
    return ObservationOrchestrator(Settings.from_env()).run()


if __name__ == "__main__":
    raise SystemExit(main())
