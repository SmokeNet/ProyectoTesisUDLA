"""Configuracion centralizada y validada."""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_local_env(path: Path | None = None) -> None:
    """Carga un archivo KEY=VALUE local sin reemplazar variables del proceso."""
    env_path = path or ROOT / "docker" / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


def env_int(name: str, default: int, minimum: int = 0) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as error:
        raise ValueError(f"{name} debe ser entero") from error
    if value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}")
    return value


def env_float(name: str, default: float, minimum: float = 0.0) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as error:
        raise ValueError(f"{name} debe ser numerico") from error
    if value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    api_base_url: str
    api_write_key: str
    monitored_url: str
    service_name: str
    server_name: str
    expected_text: str
    latency_threshold_ms: float
    timeout_ms: int
    evidence_dir: Path
    rules_file: Path
    compose_file: Path
    max_remediation_attempts: int
    remediation_cooldown_seconds: int
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_to: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_local_env()
        return cls(
            api_base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
            api_write_key=os.getenv("API_WRITE_KEY", ""),
            monitored_url=os.getenv("URL_MONITOREADA", "http://127.0.0.1:8080/"),
            service_name=os.getenv("MONITORED_SERVICE", "sitio-vigilado"),
            server_name=os.getenv("MONITORED_SERVER", "localhost"),
            expected_text=os.getenv("MONITOR_EXPECTED_TEXT", "Servicio web vigilado operativo"),
            latency_threshold_ms=env_float("LATENCY_THRESHOLD_MS", 1500, 1),
            timeout_ms=env_int("MONITOR_TIMEOUT_MS", 30000, 100),
            evidence_dir=Path(os.getenv("EVIDENCE_DIR", ROOT / "evidencias")),
            rules_file=Path(os.getenv("DETECTION_RULES_FILE", ROOT / "config" / "detection_rules.json")),
            compose_file=ROOT / "docker" / "docker-compose.yml",
            max_remediation_attempts=env_int("MAX_REMEDIATION_ATTEMPTS", 2, 1),
            remediation_cooldown_seconds=env_int("REMEDIATION_COOLDOWN_SECONDS", 300, 0),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=env_int("SMTP_PORT", 587, 1),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "")),
            smtp_to=os.getenv("SMTP_TO", ""),
        )
