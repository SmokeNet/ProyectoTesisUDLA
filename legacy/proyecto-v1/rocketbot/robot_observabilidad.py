"""Adaptador RPA: prepara plataforma y delega logica al nucleo observable."""

import json
import os
import subprocess
import sys
import time
import webbrowser
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observability.api_client import ApiClient, ApiClientError  # noqa: E402
from observability.config import Settings  # noqa: E402
from observability.continuity import ContinuityManager  # noqa: E402
from observability.evidence import EvidenceStore  # noqa: E402
from observability.logging_config import configure_logging  # noqa: E402


def bootstrap(settings: Settings) -> dict[str, object]:
    command = ["docker", "compose", "-f", str(settings.compose_file), "up", "--build", "-d"]
    started = time.perf_counter()
    try:
        process = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        return {
            "command": command,
            "exit_code": process.returncode,
            "stdout": process.stdout[-5000:],
            "stderr": process.stderr[-5000:],
            "duration_ms": (time.perf_counter() - started) * 1000,
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "command": command,
            "exit_code": -1,
            "stderr": str(error),
            "duration_ms": (time.perf_counter() - started) * 1000,
        }


def wait_readiness(client: ApiClient, attempts: int = 20) -> dict[str, object]:
    errors: list[str] = []
    for attempt in range(1, attempts + 1):
        try:
            result = client.request("GET", "/api/v1/health")
            if result.get("estado") == "ok":
                return {"status": "ok", "attempt": attempt, "response": result}
        except ApiClientError as error:
            errors.append(str(error))
        time.sleep(2)
    return {"status": "error", "attempt": attempts, "errors": errors[-3:]}


def ejecutar_flujo() -> int:
    configure_logging()
    settings = Settings.from_env()
    evidence = EvidenceStore(settings.evidence_dir)
    flow_id = f"rocketbot-{uuid4()}"
    steps: list[dict[str, object]] = []

    platform = bootstrap(settings)
    steps.append({"step": "bootstrap", **platform})
    if platform["exit_code"] != 0:
        evidence.write_json(flow_id, {"status": "error", "steps": steps}, "flujo")
        return 1

    client = ApiClient(settings.api_base_url, settings.api_write_key)
    readiness = wait_readiness(client)
    steps.append({"step": "readiness", **readiness})
    if readiness["status"] != "ok":
        evidence.write_json(flow_id, {"status": "error", "steps": steps}, "flujo")
        return 1

    try:
        client.heartbeat(
            {
                "service": "rocketbot",
                "service_type": "rpa",
                "server": settings.server_name,
                "target": "rocketbot/ejecutar_flujo_completo.bat",
                "status": "saludable",
            }
        )
    except ApiClientError:
        pass

    if os.getenv("OPEN_BROWSER", "true").lower() == "true":
        steps.append(
            {
                "step": "dashboard",
                "opened": webbrowser.open(os.getenv("DASHBOARD_URL", "http://127.0.0.1:5500/")),
            }
        )

    result = ContinuityManager(settings).run()
    steps.append({"step": "observation_continuity", "exit_code": result})
    artifact = evidence.write_json(
        flow_id,
        {"status": "ok" if result == 0 else "error", "steps": steps},
        "flujo",
    )
    print(json.dumps({"flow_id": flow_id, "evidence": asdict(artifact), "exit_code": result}, default=str))
    return result


if __name__ == "__main__":
    raise SystemExit(ejecutar_flujo())
