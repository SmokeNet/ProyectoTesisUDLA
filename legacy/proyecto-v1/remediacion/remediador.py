"""Adaptador CLI para una remediacion controlada y revalidada."""

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observability.config import Settings  # noqa: E402
from observability.logging_config import configure_logging  # noqa: E402
from observability.monitoring import SyntheticProbe  # noqa: E402
from observability.remediation import RemediationEngine, RemediationPolicy  # noqa: E402


def ejecutar_remediacion() -> bool:
    settings = Settings.from_env()
    probe = SyntheticProbe(settings)
    before = probe.observe()
    engine = RemediationEngine(
        settings.compose_file,
        RemediationPolicy(settings.max_remediation_attempts, settings.remediation_cooldown_seconds),
    )
    result = engine.execute(
        os.getenv("REMEDIATION_STRATEGY", "restart_service"),
        os.getenv("REMEDIATION_SERVICE", settings.service_name),
        before,
        probe.observe,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return result.success


if __name__ == "__main__":
    configure_logging()
    raise SystemExit(0 if ejecutar_remediacion() else 1)
