"""Persistencia del dominio operacional."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import models
import schemas


def create_event(db: Session, payload: schemas.EventCreate) -> models.EventoOperacion:
    event = models.EventoOperacion(
        id=payload.id,
        detectado_en=payload.detected_at,
        recuperado_en=payload.recovered_at,
        servidor=payload.server,
        servicio=payload.service,
        tipo_incidente=payload.incident_type,
        nivel=payload.level,
        severidad=payload.severity,
        causa=payload.cause,
        diagnostico=payload.diagnosis,
        accion_ejecutada=payload.action_executed,
        resultado=payload.result,
        tiempo_deteccion_ms=payload.detection_time_ms,
        tiempo_ejecucion_ms=payload.execution_time_ms,
        tiempo_recuperacion_ms=payload.recovery_time_ms,
        usuario=payload.user,
        robot_responsable=payload.robot,
        estado_final=payload.final_status,
        hash_evidencia=payload.evidence_hash,
        ruta_evidencia=payload.evidence_path,
        observacion=payload.observation,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(
    db: Session,
    limit: int,
    offset: int,
    status: str | None = None,
    level: str | None = None,
) -> tuple[list[models.EventoOperacion], int]:
    filters = [models.EventoOperacion.estado_final == status] if status else []
    if level:
        filters.append(models.EventoOperacion.nivel == level)
    total = db.scalar(select(func.count(models.EventoOperacion.id)).where(*filters)) or 0
    query = (
        select(models.EventoOperacion)
        .where(*filters)
        .order_by(models.EventoOperacion.detectado_en.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(query)), total


def create_metric(db: Session, payload: schemas.MetricCreate) -> models.Metrica:
    metric = models.Metrica(
        servicio=payload.service,
        nombre=payload.name,
        valor=payload.value,
        unidad=payload.unit,
        etiquetas=payload.labels,
        registrada_en=payload.recorded_at or datetime.now(timezone.utc),
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def upsert_heartbeat(db: Session, payload: schemas.HeartbeatCreate) -> models.Servicio:
    service = db.get(models.Servicio, payload.service)
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    if service is None:
        service = models.Servicio(
            nombre=payload.service,
            tipo=payload.service_type,
            servidor=payload.server,
            objetivo=payload.target,
        )
        db.add(service)
    service.estado_actual = payload.status
    service.ultimo_heartbeat = timestamp
    service.actualizado_en = timestamp
    # Sin una relacion ORM explicita SQLAlchemy no puede ordenar con certeza el
    # INSERT padre antes de las metricas hijas. El flush hace efectiva la FK.
    db.flush()
    if payload.latency_ms is not None:
        db.add(
            models.Metrica(
                servicio=payload.service,
                nombre="latency_ms",
                valor=payload.latency_ms,
                unidad="ms",
                etiquetas={"source": "heartbeat"},
                registrada_en=timestamp,
            )
        )
    db.add(
        models.Metrica(
            servicio=payload.service,
            nombre="availability",
            valor=1.0 if payload.status == "saludable" else 0.0,
            unidad="ratio",
            etiquetas={"status": payload.status},
            registrada_en=timestamp,
        )
    )
    db.commit()
    db.refresh(service)
    return service


def add_evidence(db: Session, event_id: str, payload: schemas.EvidenceCreate) -> models.Evidencia:
    evidence = models.Evidencia(
        evento_id=event_id,
        tipo=payload.kind,
        sha256=payload.sha256,
        ruta=payload.path,
        content_type=payload.content_type,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def add_remediation(db: Session, event_id: str, payload: schemas.RemediationCreate) -> models.IntentoRemediacion:
    remediation = models.IntentoRemediacion(
        evento_id=event_id,
        estrategia=payload.strategy,
        intento=payload.attempt,
        ejecutada=payload.attempted,
        exitosa=payload.success,
        escalada=payload.escalated,
        motivo=payload.reason,
        accion=payload.action,
        duracion_ms=payload.duration_ms,
        estado_antes=payload.state_before,
        estado_despues=payload.state_after,
    )
    db.add(remediation)
    event = db.get(models.EventoOperacion, event_id)
    if event is not None:
        event.accion_ejecutada = payload.action
        event.resultado = payload.reason
        event.tiempo_ejecucion_ms = payload.duration_ms
        event.estado_final = "resuelto" if payload.success else "escalado"
        if payload.success:
            event.recuperado_en = datetime.now(timezone.utc)
            event.tiempo_recuperacion_ms = max(
                0,
                (event.recuperado_en - event.detectado_en.replace(tzinfo=timezone.utc)).total_seconds() * 1000,
            )
    db.commit()
    db.refresh(remediation)
    return remediation


def summary(db: Session, hours: int = 24) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    events = list(db.scalars(select(models.EventoOperacion).where(models.EventoOperacion.detectado_en >= since)))
    metrics = list(
        db.scalars(
            select(models.Metrica)
            .where(models.Metrica.nombre == "availability", models.Metrica.registrada_en >= since)
            .order_by(models.Metrica.registrada_en)
        )
    )
    remediations = list(
        db.scalars(select(models.IntentoRemediacion).where(models.IntentoRemediacion.iniciado_en >= since))
    )
    availability = sum(metric.valor for metric in metrics) / len(metrics) * 100 if metrics else 0.0
    recovered = [event.tiempo_recuperacion_ms for event in events if event.tiempo_recuperacion_ms is not None]
    detection = [event.tiempo_deteccion_ms for event in events]
    successful = sum(1 for item in remediations if item.exitosa)
    failed = sum(1 for item in remediations if item.ejecutada and not item.exitosa)
    buckets: dict[str, dict[str, Any]] = {}
    for event in events:
        key = event.detectado_en.date().isoformat()
        bucket = buckets.setdefault(key, {"date": key, "incidents": 0, "resolved": 0})
        bucket["incidents"] += 1
        bucket["resolved"] += int(event.estado_final == "resuelto")
    return {
        "generated_at": datetime.now(timezone.utc),
        "availability_percent": round(availability, 2),
        "active_incidents": sum(1 for event in events if event.estado_final == "abierto"),
        "total_incidents": len(events),
        "mttr_ms": round(sum(recovered) / len(recovered), 2) if recovered else None,
        "mttd_ms": round(sum(detection) / len(detection), 2) if detection else None,
        "remediation_count": len(remediations),
        "remediation_success_rate": round(successful / len(remediations) * 100, 2) if remediations else 0.0,
        "services": db.scalar(select(func.count(models.Servicio.nombre))) or 0,
        "operational_incidents": sum(1 for event in events if event.nivel == "operacional"),
        "security_incidents": sum(1 for event in events if event.nivel == "seguridad"),
        "successful_remediations": successful,
        "failed_remediations": failed,
        "escalated_events": sum(1 for event in events if event.estado_final == "escalado"),
        "trend": list(buckets.values()),
    }
