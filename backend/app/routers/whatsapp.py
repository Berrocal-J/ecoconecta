import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.security import require_roles
from app.models.conversacion import WhatsAppMensajeSaliente
from app.models.cuenta_acceso import RolAcceso
from app.models.historial import WhatsAppEvento
from app.services.conversacion_service import ConversationService
from app.services.outbound_service import retry_pending_messages
from app.services.voice_service import VoiceService, VoiceSimulator
from app.services.whatsapp_service import WhatsAppSimulator, normalize_phone, whatsapp_service

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
voice_service = VoiceService() if settings.USE_EXTERNAL_SERVICES and settings.OPENAI_API_KEY else VoiceSimulator()


@router.get("/webhook", response_class=PlainTextResponse)
def verificar_webhook(request: Request):
    if whatsapp_service.verificar_webhook(request.query_params.get("hub.mode", ""), request.query_params.get("hub.verify_token", "")):
        return request.query_params.get("hub.challenge", "")
    raise HTTPException(status_code=403, detail="Verificacion fallida")


def _signature_is_valid(raw_body: bytes, request: Request) -> bool:
    if not settings.USE_EXTERNAL_SERVICES:
        return True  # modo simulador: no hay Meta de por medio
    if not settings.WHATSAPP_APP_SECRET:
        return False  # con Meta real la firma es obligatoria
    received = request.headers.get("x-hub-signature-256", "")
    expected = "sha256=" + hmac.new(settings.WHATSAPP_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)


def _save_event(db: Session, message_id: str, phone: str, kind: str, payload: dict) -> bool:
    event = WhatsAppEvento(message_id=message_id, telefono=phone or "unknown", tipo=kind[:30], payload=json.dumps(payload, ensure_ascii=False), procesado=0)
    db.add(event)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


@router.post("/webhook")
async def recibir_mensaje(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    raw_body = await request.body()
    if not _signature_is_valid(raw_body, request):
        raise HTTPException(status_code=403, detail="Firma de webhook invalida")
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON invalido")

    queued = 0
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {}) or {}
            if field != "messages":
                continue
            for status in value.get("statuses", []) or []:
                status_id = f"status:{status.get('id')}:{status.get('status')}"
                _save_event(db, status_id[:180], status.get("recipient_id", ""), f"status_{status.get('status', 'unknown')}", status)
                outgoing = db.query(WhatsAppMensajeSaliente).filter(WhatsAppMensajeSaliente.wa_message_id == status.get("id")).first()
                if outgoing:
                    outgoing.estado = "enviado" if status.get("status") in {"sent", "delivered", "read"} else "fallido"
                    outgoing.error = json.dumps(status.get("errors"), ensure_ascii=False) if status.get("errors") else None
                    db.commit()
            for message in value.get("messages", []) or []:
                message_id = message.get("id")
                if not message_id:
                    continue
                phone = normalize_phone(message.get("from", ""))
                since = datetime.now(timezone.utc) - timedelta(minutes=1)
                recent = db.query(WhatsAppEvento).filter(WhatsAppEvento.telefono == phone, WhatsAppEvento.creado_en >= since).count()
                if recent >= settings.WHATSAPP_RATE_LIMIT_PER_MINUTE:
                    continue
                if _save_event(db, message_id, phone, message.get("type", "unknown"), message):
                    background_tasks.add_task(procesar_mensaje_whatsapp_background, phone, message)
                    queued += 1
    return {"status": "received", "queued": queued}


async def procesar_mensaje_whatsapp_background(phone_number: str, message: dict) -> None:
    db = SessionLocal()
    try:
        await procesar_mensaje_whatsapp(phone_number, message, db)
    finally:
        db.close()


def _interactive_text(message: dict) -> str:
    interactive = message.get("interactive", {}) or {}
    reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
    return reply.get("id") or reply.get("title") or ""


async def procesar_mensaje_whatsapp(phone_number: str, message: dict, db: Session) -> None:
    message_type = message.get("type")
    text = ""
    if message_type == "text":
        text = message.get("text", {}).get("body", "")
    elif message_type == "interactive":
        text = _interactive_text(message)
    elif message_type == "audio":
        audio_id = message.get("audio", {}).get("id")
        audio_bytes = await whatsapp_service.descargar_audio(audio_id)
        text = voice_service.transcribir_audio(audio_bytes) if audio_bytes else None
        if not text:
            await whatsapp_service.enviar_mensaje_texto(phone_number, "No pude transcribir la nota de voz. Intenta enviarla de nuevo o escribe *menu*.")
            return
    else:
        await whatsapp_service.enviar_mensaje_texto(phone_number, "Por ahora acepto texto, botones, listas y notas de voz. Escribe *menu* para ver opciones.")
        return

    if text:
        await ConversationService(db).handle(phone_number, text)
    event = db.query(WhatsAppEvento).filter(WhatsAppEvento.message_id == message.get("id")).first()
    if event:
        event.procesado = 1
        db.commit()


@router.post("/simulador/entrada")
async def simulador_entrada(payload: dict[str, Any], db: Session = Depends(get_db)):
    if settings.USE_EXTERNAL_SERVICES:
        raise HTTPException(status_code=404, detail="Simulador deshabilitado con servicios externos")
    phone = normalize_phone(payload.get("phone_number", ""))
    content = payload.get("content")
    message_type = payload.get("type", "text")
    if not phone or not content:
        raise HTTPException(status_code=400, detail="Se requiere phone_number y content")
    message = {"id": "sim_" + uuid.uuid4().hex, "type": message_type}
    if message_type == "text":
        message["text"] = {"body": content}
    elif message_type == "interactive":
        message["interactive"] = {"button_reply": {"id": content, "title": content}}
    elif message_type == "audio":
        message["audio"] = {"id": "sim_audio_id"}
    else:
        message["unsupported"] = content
    await procesar_mensaje_whatsapp(phone, message, db)
    return {"status": "simulated", "phone_number": phone}


@router.post("/cola/reintentar")
async def reintentar_cola_saliente(
    db: Session = Depends(get_db),
    account=Depends(require_roles(RolAcceso.ADMIN)),
):
    """Procesa mensajes pendientes/fallidos; puede invocarse desde un scheduler."""
    return await retry_pending_messages(db)


@router.get("/simulador/mensajes")
def obtener_mensajes_simulados(account=Depends(require_roles(RolAcceso.ADMIN))):
    if isinstance(whatsapp_service, WhatsAppSimulator):
        return {"mensajes": whatsapp_service.get_mensajes_enviados()}
    return {"mensajes": []}


@router.post("/simulador/limpiar")
def limpiar_mensajes_simulados(account=Depends(require_roles(RolAcceso.ADMIN))):
    if settings.USE_EXTERNAL_SERVICES:
        raise HTTPException(status_code=404, detail="Simulador deshabilitado con servicios externos")
    if isinstance(whatsapp_service, WhatsAppSimulator):
        whatsapp_service.clear_mensajes()
    return {"status": "cleared"}
