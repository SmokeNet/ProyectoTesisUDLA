"""Gateway defensivo del sitio vigilado.

Inspecciona metadatos y muestras acotadas antes de reenviar al sitio interno.
Las respuestas son locales, temporales y reversibles; no modifica el host.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from observability.api_client import ApiClient, ApiClientError
from observability.domain import FinalStatus, OperationalEvent
from observability.evidence import EvidenceStore
from observability.security import HttpAccessEvent, SecurityDetection, SecurityPolicy, SecurityWatcher

LOGGER = logging.getLogger("security-gateway")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
MAX_BODY_BYTES = 64 * 1024
UPSTREAM = os.getenv("UPSTREAM_URL", "http://sitio-vigilado").rstrip("/")
SERVICE = "security-watcher"
base_policy = SecurityPolicy.from_file(os.getenv("SECURITY_RULES_FILE", "/app/config/security_rules.json"))
watcher = SecurityWatcher(replace(
    base_policy,
    flood_requests=int(os.getenv("SECURITY_FLOOD_REQUESTS", str(base_policy.flood_requests))),
    temporary_block_seconds=int(os.getenv("SECURITY_BLOCK_SECONDS", str(base_policy.temporary_block_seconds))),
))
api = ApiClient(os.getenv("API_BASE_URL", "http://api:8000"), os.getenv("API_WRITE_KEY", ""))
evidence = EvidenceStore(Path(os.getenv("EVIDENCE_DIR", "/app/evidencias")))


def safe_api(operation, *args):
    try:
        return operation(*args)
    except ApiClientError as error:
        LOGGER.error("No fue posible auditar en API: %s", error)
        return None


def heartbeat() -> None:
    safe_api(api.heartbeat, {
        "service": SERVICE,
        "service_type": "seguridad",
        "server": "security-gateway",
        "target": UPSTREAM,
        "status": "saludable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@asynccontextmanager
async def lifespan(_: FastAPI):
    heartbeat()
    yield


app = FastAPI(title="Security Watcher Gateway", version="1.0.0", lifespan=lifespan)


def source_ip(request: Request) -> str:
    # El servicio solo se publica en loopback. No se confia en X-Forwarded-For
    # porque no existe un proxy confiable delante en este prototipo.
    peer = request.client.host if request.client else "desconocido"
    demo_source = request.headers.get("x-demo-source", "")
    # El puerto Docker se publica exclusivamente en loopback, aunque NAT hace
    # visible al host como gateway de la red bridge dentro del contenedor.
    if (
        os.getenv("SECURITY_DEMO_MODE", "false").lower() == "true"
        and demo_source
        and len(demo_source) <= 64
        and all(character.isalnum() or character in ".:_-" for character in demo_source)
    ):
        return f"demo:{demo_source}"
    return peer


def persist_detection(access: HttpAccessEvent, detection: SecurityDetection) -> None:
    event = OperationalEvent(
        server="security-gateway",
        service=SERVICE,
        incident_type=detection.incident_type,
        level="seguridad",
        severity=detection.severity,
        cause=detection.cause,
        diagnosis=detection.diagnosis,
        robot="security-watcher",
        final_status=FinalStatus.OPEN,
        observation={"access": access.safe_dict(), "rule_id": detection.rule_id},
    )
    payload = event.as_dict()
    artifact = evidence.write_json(event.id, payload, "evento-seguridad")
    event.evidence_hash = artifact.sha256
    event.evidence_path = str(artifact.path)
    created = safe_api(api.create_event, event.as_dict())
    if not created:
        return
    safe_api(api.create_evidence, event.id, {
        "kind": artifact.kind,
        "path": str(artifact.path),
        "sha256": artifact.sha256,
        "content_type": artifact.content_type,
    })
    applied = detection.response in {"temporary_block", "rate_limit"}
    safe_api(api.create_remediation, event.id, {
        "strategy": detection.response,
        "attempt": 1,
        "attempted": applied,
        "success": applied,
        "escalated": not applied,
        "reason": "respuesta defensiva temporal aplicada" if applied else "requiere analisis humano",
        "action": detection.response,
        "duration_ms": 0,
        "state_before": {"blocked": False},
        "state_after": {"blocked": applied, "scope": "memoria del gateway"},
    })


def proxy(method: str, path: str, body: bytes, request: Request) -> Response:
    headers = {"Accept": request.headers.get("accept", "*/*")}
    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]
    upstream_request = UrlRequest(
        f"{UPSTREAM}{path}", data=body or None, headers=headers, method=method
    )
    try:
        with urlopen(upstream_request, timeout=5) as upstream:
            content_type = upstream.headers.get("Content-Type", "application/octet-stream")
            return Response(upstream.read(), status_code=upstream.status, media_type=content_type)
    except HTTPError as error:
        return Response(error.read(), status_code=error.code, media_type=error.headers.get_content_type())
    except (URLError, TimeoutError):
        return JSONResponse({"detail": "sitio vigilado no disponible"}, status_code=502)


@app.get("/_security/health")
def health() -> dict[str, str]:
    return {"estado": "ok", "componente": SERVICE, "modo": "defensivo-controlado"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"])
async def inspect_and_proxy(path: str, request: Request) -> Response:
    ip = source_ip(request)
    expiry = watcher.blocked_until(ip)
    if expiry:
        return JSONResponse(
            {"detail": "bloqueo defensivo temporal", "blocked_until": expiry.isoformat()},
            status_code=429,
            headers={"Retry-After": str(max(1, int((expiry - datetime.now(timezone.utc)).total_seconds())))},
        )
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        return JSONResponse({"detail": "solicitud excede limite defensivo"}, status_code=413)
    raw_path = "/" + path
    if request.url.query:
        raw_path += "?" + request.url.query
    access = HttpAccessEvent(
        source_ip=ip,
        method=request.method,
        path=raw_path,
        user_agent=request.headers.get("user-agent", ""),
        body_sample=body.decode("utf-8", errors="replace"),
    )
    detections = watcher.evaluate(access)
    for detection in detections:
        persist_detection(access, detection)
    if detections:
        status = 429 if any(item.response == "rate_limit" for item in detections) else 403
        return JSONResponse({
            "detail": "solicitud rechazada por politica defensiva",
            "rules": [item.rule_id for item in detections],
            "temporary": True,
        }, status_code=status)
    return proxy(request.method, raw_path, body, request)
