"""Generacion inmutable de evidencia con hash SHA-256."""

import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .domain import EvidenceArtifact


class EvidenceStore:
    def __init__(self, root: Path):
        self.root = root

    def _directory(self, event_id: str) -> Path:
        directory = self.root / "eventos" / event_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def _artifact(kind: str, path: Path, content_type: str) -> EvidenceArtifact:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return EvidenceArtifact(kind=kind, path=path, sha256=digest, content_type=content_type)

    def register_file(self, kind: str, path: Path, content_type: str) -> EvidenceArtifact:
        """Calcula el hash de un artefacto producido por otra herramienta."""
        return self._artifact(kind, path, content_type)

    def write_json(self, event_id: str, payload: dict[str, Any], name: str = "evento") -> EvidenceArtifact:
        path = self._directory(event_id) / f"{name}.json"
        envelope = {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "event_id": event_id,
            "payload": payload,
        }
        path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")
        return self._artifact("json", path, "application/json")

    def write_log(self, event_id: str, content: str, name: str = "comando") -> EvidenceArtifact:
        path = self._directory(event_id) / f"{name}.log"
        path.write_text(content, encoding="utf-8")
        return self._artifact("log", path, "text/plain")

    def write_html_report(self, event_id: str, payload: dict[str, Any]) -> EvidenceArtifact:
        rows = "".join(
            f"<tr><th>{html.escape(str(key))}</th><td><pre>{html.escape(str(value))}</pre></td></tr>"
            for key, value in payload.items()
        )
        document = (
            "<!doctype html><html lang='es'><meta charset='utf-8'>"
            f"<title>Evidencia {html.escape(event_id)}</title>"
            "<style>body{font-family:system-ui;margin:2rem}table{border-collapse:collapse}"
            "th,td{border:1px solid #bbb;padding:.5rem;text-align:left}pre{white-space:pre-wrap}</style>"
            f"<h1>Evidencia operacional</h1><p>ID: {html.escape(event_id)}</p><table>{rows}</table></html>"
        )
        path = self._directory(event_id) / "reporte.html"
        path.write_text(document, encoding="utf-8")
        return self._artifact("html", path, "text/html")
