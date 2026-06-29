"""Motor de estrategias seguras, acotadas y verificables."""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .domain import Observation, RemediationResult

Verifier = Callable[[], Observation]


@dataclass(frozen=True, slots=True)
class RemediationPolicy:
    max_attempts: int = 2
    cooldown_seconds: int = 300
    timeout_seconds: int = 120


class RemediationEngine:
    """Traduce estrategias conocidas a comandos predefinidos; nunca usa shell."""

    MUTATING_STRATEGIES = {"restart_service", "start_service", "restart_api", "start_mysql", "activate_backup"}
    ESCALATION_STRATEGIES = {"escalate", "validate_deployment"}
    SERVICE_MAP = {
        "sitio-vigilado": "sitio-vigilado",
        "api": "api",
        "mysql": "mysql",
    }

    def __init__(
        self,
        compose_file: Path,
        policy: RemediationPolicy,
        state_file: Path | None = None,
    ):
        self.compose_file = compose_file
        self.policy = policy
        self.state_file = state_file or compose_file.parents[1] / "evidencias" / "remediation_state.json"

    def _load_state(self, key: str) -> tuple[int, datetime | None]:
        if not self.state_file.exists():
            return 0, None
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8")).get(key, {})
            timestamp = datetime.fromisoformat(data["last_attempt_at"]) if data.get("last_attempt_at") else None
            return int(data.get("attempt_count", 0)), timestamp
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return 0, None

    def _save_state(self, key: str, attempt_count: int) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            all_state = json.loads(self.state_file.read_text(encoding="utf-8")) if self.state_file.exists() else {}
        except (OSError, json.JSONDecodeError):
            all_state = {}
        all_state[key] = {
            "attempt_count": attempt_count,
            "last_attempt_at": datetime.now(timezone.utc).isoformat(),
        }
        temporary = self.state_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(all_state, indent=2), encoding="utf-8")
        temporary.replace(self.state_file)

    def _command(self, strategy: str, service: str) -> list[str] | None:
        if strategy == "activate_backup":
            return [
                "docker",
                "compose",
                "-f",
                str(self.compose_file),
                "--profile",
                "continuidad",
                "up",
                "-d",
                "sitio-respaldo",
            ]
        mapped = self.SERVICE_MAP.get(service)
        if strategy == "restart_api":
            mapped = "api"
        elif strategy == "start_mysql":
            mapped = "mysql"
        if strategy not in self.MUTATING_STRATEGIES or mapped is None:
            return None
        command = ["docker", "compose", "-f", str(self.compose_file), "up", "-d", "--no-deps"]
        if strategy in {"restart_service", "restart_api"}:
            command.append("--force-recreate")
        command.append(mapped)
        return command

    def execute(
        self,
        strategy: str,
        service: str,
        before: Observation,
        verifier: Verifier,
        attempt_count: int | None = None,
        last_attempt_at: datetime | None = None,
    ) -> RemediationResult:
        before_state = before.as_dict()
        state_key = f"{service}:{strategy}"
        if attempt_count is None:
            attempt_count, persisted_last_attempt = self._load_state(state_key)
            last_attempt_at = last_attempt_at or persisted_last_attempt
        if last_attempt_at is not None:
            age = (datetime.now(timezone.utc) - last_attempt_at).total_seconds()
            attempt_window = max(3600, self.policy.cooldown_seconds * 6)
            if age >= attempt_window:
                attempt_count = 0
                last_attempt_at = None
        if attempt_count >= self.policy.max_attempts:
            return RemediationResult(
                strategy, False, False, True, "limite de intentos alcanzado", "escalar", 0, before_state, {}
            )
        if last_attempt_at is not None:
            age = (datetime.now(timezone.utc) - last_attempt_at).total_seconds()
            if age < self.policy.cooldown_seconds:
                return RemediationResult(
                    strategy, False, False, True, "cooldown activo", "escalar", 0, before_state, {}
                )
        command = self._command(strategy, service)
        if command is None:
            return RemediationResult(
                strategy,
                False,
                False,
                True,
                "estrategia requiere intervencion humana",
                "escalar",
                0,
                before_state,
                {},
            )

        started = time.perf_counter()
        try:
            process = subprocess.run(
                command,
                cwd=self.compose_file.parents[1],
                capture_output=True,
                text=True,
                timeout=self.policy.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            self._save_state(state_key, attempt_count + 1)
            return RemediationResult(
                strategy,
                True,
                False,
                True,
                str(error),
                " ".join(command),
                (time.perf_counter() - started) * 1000,
                before_state,
                {},
            )
        if process.returncode != 0:
            self._save_state(state_key, attempt_count + 1)
            reason = (process.stderr or process.stdout or "comando fallido")[:1000]
            return RemediationResult(
                strategy,
                True,
                False,
                True,
                reason,
                " ".join(command),
                (time.perf_counter() - started) * 1000,
                before_state,
                {},
            )

        after = verifier()
        success = (
            not bool(after.error_kind)
            and after.port_open is not False
            and after.http_status not in range(400, 600)
        )
        self._save_state(state_key, 0 if success else attempt_count + 1)
        return RemediationResult(
            strategy=strategy,
            attempted=True,
            success=success,
            escalated=not success,
            reason="revalidacion exitosa" if success else "la falla persiste despues de la accion",
            action=" ".join(command),
            duration_ms=(time.perf_counter() - started) * 1000,
            state_before=before_state,
            state_after=after.as_dict(),
        )
