"""Persistent, best-effort outbound WhatsApp delivery records."""
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.conversacion import WhatsAppMensajeSaliente
from app.services.whatsapp_service import whatsapp_service
from app.core.config import settings


async def send_text_logged(db: Session, destination: str, body: str, solicitud_id: int | None = None) -> WhatsAppMensajeSaliente:
    message = WhatsAppMensajeSaliente(destino=destination, tipo="text", contenido=body, solicitud_id=solicitud_id, estado="pendiente")
    db.add(message)
    db.commit()
    db.refresh(message)
    message.intentos += 1
    result = await whatsapp_service.enviar_mensaje_texto(destination, body)
    if result.get("success") is False or result.get("error"):
        message.estado = "fallido"
        message.error = "Error de entrega Cloud API"
    else:
        message.estado = "enviado"
        message.wa_message_id = result.get("messages", [{}])[0].get("id") or result.get("message_id")
        message.enviado_en = datetime.now(timezone.utc)
    db.commit()
    return message


async def send_notification_logged(
    db: Session,
    destination: str,
    body: str,
    template_name: str = "",
    solicitud_id: int | None = None,
) -> WhatsAppMensajeSaliente:
    message = WhatsAppMensajeSaliente(
        destino=destination,
        tipo="template" if template_name else "text",
        contenido=body,
        plantilla=template_name or None,
        solicitud_id=solicitud_id,
        estado="pendiente",
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    message.intentos += 1
    result = await whatsapp_service.enviar_notificacion(destination, body, template_name)
    if result.get("success") is False or result.get("error"):
        message.estado = "fallido"
        message.error = "Error de entrega Cloud API"
    else:
        message.estado = "enviado"
        message.wa_message_id = result.get("messages", [{}])[0].get("id") or result.get("message_id")
        message.enviado_en = datetime.now(timezone.utc)
    db.commit()
    return message


async def retry_pending_messages(db: Session, limit: int = 50) -> dict[str, int]:
    """Reintenta mensajes pendientes/fallidos con backoff acotado."""
    now = datetime.now(timezone.utc)
    candidates = db.query(WhatsAppMensajeSaliente).filter(
        WhatsAppMensajeSaliente.estado.in_(["pendiente", "fallido"]),
        WhatsAppMensajeSaliente.intentos < settings.WHATSAPP_MAX_RETRIES,
    ).order_by(WhatsAppMensajeSaliente.creado_en.asc()).limit(limit).all()
    retried = sent = failed = 0
    for message in candidates:
        if message.actualizado_en and message.actualizado_en.tzinfo:
            wait_seconds = min(30, 2 ** max(message.intentos - 1, 0))
            if now - message.actualizado_en < timedelta(seconds=wait_seconds):
                continue
        message.intentos += 1
        if message.plantilla:
            result = await whatsapp_service.enviar_mensaje_template(message.destino, message.plantilla)
        else:
            result = await whatsapp_service.enviar_mensaje_texto(message.destino, message.contenido or "")
        retried += 1
        if result.get("success") is False or result.get("error"):
            message.estado = "fallido"
            message.error = "Error de entrega Cloud API"
            failed += 1
        else:
            message.estado = "enviado"
            message.error = None
            message.wa_message_id = result.get("messages", [{}])[0].get("id") or result.get("message_id")
            message.enviado_en = now
            sent += 1
        db.commit()
    return {"reintentados": retried, "enviados": sent, "fallidos": failed}
