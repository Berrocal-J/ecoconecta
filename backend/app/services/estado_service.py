from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.historial import HistorialEstado
from app.models.solicitud import EstadoSolicitud, Solicitud


ALLOWED_TRANSITIONS = {
    EstadoSolicitud.RECIBIDA: {EstadoSolicitud.EN_REVISION, EstadoSolicitud.CANCELADA},
    EstadoSolicitud.EN_REVISION: {EstadoSolicitud.ASIGNADA, EstadoSolicitud.CANCELADA},
    EstadoSolicitud.ASIGNADA: {EstadoSolicitud.PROGRAMADA, EstadoSolicitud.CANCELADA},
    EstadoSolicitud.PROGRAMADA: {EstadoSolicitud.RECOLECTADA, EstadoSolicitud.CANCELADA},
    EstadoSolicitud.RECOLECTADA: set(),
    EstadoSolicitud.CANCELADA: set(),
}


def path_to(current: EstadoSolicitud, target: EstadoSolicitud) -> list[EstadoSolicitud]:
    if current == target:
        return []
    path = [
        EstadoSolicitud.RECIBIDA,
        EstadoSolicitud.EN_REVISION,
        EstadoSolicitud.ASIGNADA,
        EstadoSolicitud.PROGRAMADA,
        EstadoSolicitud.RECOLECTADA,
    ]
    if target == EstadoSolicitud.CANCELADA:
        return [target]
    try:
        start = path.index(current)
        end = path.index(target)
    except ValueError as error:
        raise HTTPException(status_code=409, detail="Transición de estado no permitida") from error
    if end < start:
        raise HTTPException(status_code=409, detail="No se puede retroceder el estado")
    return path[start + 1:end + 1]


def advance(db: Session, solicitud: Solicitud, target: EstadoSolicitud, account_id: int | None = None, observation: str | None = None) -> None:
    for next_state in path_to(solicitud.estado, target):
        previous = solicitud.estado.value
        solicitud.estado = next_state
        db.add(HistorialEstado(solicitud_id=solicitud.id, estado_anterior=previous, estado_nuevo=next_state.value, cuenta_id=account_id, observacion=observation))
