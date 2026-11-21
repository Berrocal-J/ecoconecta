"""Stateful WhatsApp conversation for citizens.

The conversation state is persisted in PostgreSQL. The service deliberately
keeps operational decisions out of the model: it only collects and guides the
citizen until an explicit confirmation.
"""
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.colectivo import Colectivo, TipoColectivo
from app.models.conversacion import Contenido, SolicitudEliminacion, UsuarioPiloto, WhatsAppConversacion
from app.models.historial import HistorialEstado, WhatsAppBorrador
from app.models.asignacion import Asignacion
from app.models.puntuacion import PuntuacionHistorial
from app.models.solicitud import EstadoSolicitud, Solicitud, TipoResiduo
from app.models.usuario import TipoGenerador, Usuario
from app.services.whatsapp_service import whatsapp_service
from app.services.outbound_service import send_text_logged


MENU_TEXT = (
    "🌱 EcoConecta Villas de San Pablo\n\n"
    "Elige una opción:\n"
    "1. Aprender a separar residuos\n"
    "2. Solicitar recolección\n"
    "3. Consultar mi solicitud\n"
    "4. Ver mis puntos\n"
    "5. Horarios y rutas\n"
    "6. Hablar con el colectivo\n\n"
    "Puedes escribir *menu* en cualquier momento."
)


def normalizar_telefono(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 10 and digits.startswith("3"):
        digits = "57" + digits
    return digits


def normalizar_texto(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", (value or "").lower())
        if unicodedata.category(c) != "Mn"
    ).strip()


class ConversationService:
    def __init__(self, db: Session, sender=whatsapp_service):
        self.db = db
        self.sender = sender

    def _conversation(self, phone: str) -> WhatsAppConversacion:
        conversation = self.db.query(WhatsAppConversacion).filter(
            WhatsAppConversacion.telefono == phone
        ).first()
        now = datetime.now(timezone.utc)
        if not conversation:
            conversation = WhatsAppConversacion(telefono=phone, estado_conversacion="inicio")
            self.db.add(conversation)
            self.db.flush()
        elif conversation.ultima_interaccion and conversation.ultima_interaccion < now - timedelta(minutes=settings.WHATSAPP_CONVERSATION_TTL_MINUTES):
            conversation.estado_conversacion = "inicio"
            conversation.set_context({})
        conversation.ultima_interaccion = now
        return conversation

    async def _text(self, phone: str, message: str) -> None:
        if self.sender is whatsapp_service:
            await send_text_logged(self.db, phone, message)
        else:
            await self.sender.enviar_mensaje_texto(phone, message)

    async def _menu(self, phone: str, conversation: WhatsAppConversacion) -> None:
        conversation.estado_conversacion = "menu"
        self.db.commit()
        if hasattr(self.sender, "enviar_mensaje_lista"):
            await self.sender.enviar_mensaje_lista(
                phone,
                "Menú EcoConecta",
                "Selecciona una opción",
                [
                    {"id": "aprender", "title": "Aprender a separar"},
                    {"id": "solicitar", "title": "Solicitar recolección"},
                    {"id": "consultar", "title": "Consultar solicitud"},
                    {"id": "puntos", "title": "Ver mis puntos"},
                    {"id": "horarios", "title": "Horarios y rutas"},
                    {"id": "colectivo", "title": "Hablar con colectivo"},
                ],
            )
        else:
            await self._text(phone, MENU_TEXT)

    def _is_yes(self, text: str) -> bool:
        return normalizar_texto(text) in {"si", "sí", "acepto", "aceptar", "1", "confirmar", "confirmo"}

    def _is_no(self, text: str) -> bool:
        return normalizar_texto(text) in {"no", "rechazo", "rechazar", "2", "cancelar", "cancelo"}

    def _save_draft(self, phone: str, context: dict, text: str = "") -> None:
        """Mirrors incomplete conversational data to the explicit draft table."""
        if not context or not any(context.get(key) for key in ("tipo_residuo", "direccion", "horario", "observaciones")):
            return
        draft = self.db.query(WhatsAppBorrador).filter(WhatsAppBorrador.telefono == phone).first()
        if not draft:
            draft = WhatsAppBorrador(telefono=phone)
            self.db.add(draft)
        draft.tipo_generador = context.get("tipo_generador")
        draft.tipo_residuo = context.get("tipo_residuo")
        draft.direccion = context.get("direccion")
        draft.horario = context.get("horario")
        draft.observaciones = context.get("observaciones")
        draft.ultimo_texto = text[:1000] if text else draft.ultimo_texto

    def _flow(self, text: str) -> str | None:
        value = normalizar_texto(text)
        if "mixto" in value:
            return "mixto"
        if any(word in value for word in ("organico", "comida", "poda", "cascara", "huerta")):
            return "organico"
        if any(word in value for word in ("reciclable", "plastico", "carton", "vidrio", "metal", "papel")):
            return "reciclable"
        return None

    async def handle(self, phone_number: str, text: str) -> None:
        phone = normalizar_telefono(phone_number)
        text = (text or "").strip()
        if not text:
            await self._text(phone, "No recibí texto. Puedes escribir *menu* para comenzar.")
            return

        conversation = self._conversation(phone)
        context = conversation.get_context()
        self._save_draft(phone, context, text)
        normalized = normalizar_texto(text)

        if normalized in {"borrar mis datos", "eliminar mis datos", "borrar datos"}:
            self.db.add(SolicitudEliminacion(telefono=phone, motivo="Solicitud recibida por WhatsApp"))
            self.db.commit()
            await self._text(phone, "Recibimos tu solicitud de eliminación. El administrador la revisará y te confirmará por este canal.")
            return

        if normalized in {"menu", "inicio", "0", "volver"}:
            conversation.set_context({})
            self.db.commit()
            await self._menu(phone, conversation)
            return
        if normalized in {"cancelar", "cancel", "salir"}:
            conversation.estado_conversacion = "menu"
            conversation.set_context({})
            draft = self.db.query(WhatsAppBorrador).filter(WhatsAppBorrador.telefono == phone).first()
            if draft:
                self.db.delete(draft)
            self.db.commit()
            await self._text(phone, "Solicitud cancelada. No se creó ninguna recolección.")
            await self._menu(phone, conversation)
            return

        user = self.db.query(Usuario).filter(Usuario.whatsapp == phone).first()
        has_consent = bool(user and user.consentimiento_datos and user.consentimiento_whatsapp)

        if conversation.estado_conversacion in {"inicio", "esperando_consentimiento"} and not has_consent:
            if self._is_yes(text):
                context["consentimiento_datos"] = True
                context["consentimiento_whatsapp"] = True
                conversation.set_context(context)
                conversation.estado_conversacion = "menu"
                self.db.commit()
                await self._text(phone, "Gracias. Usaremos tus datos solo para gestionar solicitudes y avisos de EcoConecta.")
                await self._menu(phone, conversation)
            else:
                conversation.estado_conversacion = "esperando_consentimiento"
                self.db.commit()
                await self.sender.enviar_mensaje_botones(
                    phone,
                    "Antes de continuar",
                    "Usaremos tu número, nombre y dirección para gestionar la recolección y enviarte avisos. ¿Autorizas el tratamiento y las notificaciones?",
                    [{"id": "aceptar", "title": "Aceptar"}, {"id": "rechazar", "title": "No aceptar"}],
                )
            return

        if conversation.estado_conversacion == "inicio":
            await self._menu(phone, conversation)
            return

        if conversation.estado_conversacion == "menu":
            option = normalized
            if option in {"1", "aprender", "educacion", "separar"}:
                contents = self.db.query(Contenido).filter(Contenido.publicado.is_(True)).order_by(Contenido.orden, Contenido.id).limit(4).all()
                if contents:
                    await self._text(phone, "\n\n".join(f"*{item.titulo}*\n{item.cuerpo}" for item in contents))
                else:
                    await self._text(phone, "Orgánicos: cáscaras, restos de cocina y poda.\nReciclables: plástico, cartón, vidrio, metal y papel.")
                return
            if option in {"2", "solicitar", "recoleccion", "recolección"}:
                if not has_consent and not (context.get("consentimiento_datos") and context.get("consentimiento_whatsapp")):
                    conversation.estado_conversacion = "esperando_consentimiento"
                    self.db.commit()
                    await self._text(phone, "Para solicitar una recolección necesito tu autorización. Responde *acepto* para continuar.")
                    return
                if settings.MODO_PILOTO and not self.db.query(UsuarioPiloto).filter(UsuarioPiloto.whatsapp == phone, UsuarioPiloto.activo.is_(True)).first():
                    await self._text(phone, "El servicio de recolección está en piloto y este número aún no está habilitado. Puedes usar *aprender* para consultar educación ambiental.")
                    return
                conversation.estado_conversacion = "solicitando_flujo"
                context = {"consentimiento_datos": True, "consentimiento_whatsapp": True}
                if user:
                    context.update({"nombre": user.nombre, "tipo_generador": user.tipo_generador.value, "direccion": user.direccion})
                conversation.set_context(context)
                self.db.commit()
                await self.sender.enviar_mensaje_botones(phone, "Tipo de residuo", "¿Qué deseas entregar?", [{"id": "organico", "title": "Orgánicos"}, {"id": "reciclable", "title": "Reciclables"}])
                return
            if option in {"3", "consultar", "estado"}:
                await self._send_requests(phone, user)
                return
            if option in {"4", "puntos", "mis puntos"}:
                await self._send_points(phone, user)
                return
            if option in {"5", "horarios", "rutas"}:
                await self._text(phone, "Horarios y rutas son acuerdos comunitarios de referencia y están pendientes de validación de la Fundación Santo Domingo. Para solicitar, indica tu disponibilidad y el coordinador confirmará el horario.")
                return
            if option in {"6", "colectivo", "hablar"}:
                await self._text(phone, "Puedes escribir tu mensaje y lo dejaremos como observación para el coordinador del flujo. Si necesitas atención inmediata, contacta al colectivo por los canales comunitarios autorizados.")
                return
            await self._text(phone, "No reconocí esa opción.\n\n" + MENU_TEXT)
            return

        if conversation.estado_conversacion == "solicitando_flujo":
            flow = self._flow(text)
            if flow == "mixto":
                await self._text(phone, "Los residuos mixtos deben separarse. Puedo crear una solicitud orgánica y otra reciclable; escribe *organico* o *reciclable* para comenzar una de ellas.")
                return
            if not flow:
                await self._text(phone, "Indica *orgánico* o *reciclable*. También puedo ayudarte a identificarlo: cáscaras y poda son orgánicos; plástico, cartón, vidrio, metal y papel son reciclables.")
                return
            context["tipo_residuo"] = flow
            context.setdefault("mensaje_original", text)
            if not context.get("nombre"):
                conversation.estado_conversacion = "solicitando_nombre"
                await self._text(phone, "¿Cuál es tu nombre o el nombre de la unidad productiva?")
            elif not context.get("tipo_generador"):
                conversation.estado_conversacion = "solicitando_generador"
                await self._text(phone, "¿Eres un hogar o una unidad productiva?")
            elif not context.get("direccion"):
                conversation.estado_conversacion = "solicitando_direccion"
                await self._text(phone, "¿Cuál es la dirección en Villas de San Pablo?")
            else:
                conversation.estado_conversacion = "solicitando_horario"
                await self._text(phone, "¿En qué horario tienes disponibilidad?")
            conversation.set_context(context)
            self.db.commit()
            return

        if conversation.estado_conversacion == "solicitando_nombre":
            context["nombre"] = text[:100]
            conversation.estado_conversacion = "solicitando_generador"
            conversation.set_context(context)
            self.db.commit()
            await self._text(phone, "¿Eres un hogar o una unidad productiva?")
            return
        if conversation.estado_conversacion == "solicitando_generador":
            if "unidad" in normalized or "negocio" in normalized or "comercio" in normalized:
                context["tipo_generador"] = "unidad_productiva"
            elif "hogar" in normalized or normalized in {"2", "casa"}:
                context["tipo_generador"] = "hogar"
            else:
                await self._text(phone, "Responde *hogar* o *unidad productiva*.")
                return
            conversation.estado_conversacion = "solicitando_direccion"
            conversation.set_context(context)
            self.db.commit()
            await self._text(phone, "¿Cuál es la dirección en Villas de San Pablo?")
            return
        if conversation.estado_conversacion == "solicitando_direccion":
            context["direccion"] = text[:255]
            conversation.estado_conversacion = "solicitando_horario"
            conversation.set_context(context)
            self.db.commit()
            await self._text(phone, "¿En qué día y horario tienes disponibilidad?")
            return
        if conversation.estado_conversacion == "solicitando_horario":
            context["horario"] = text[:100]
            conversation.estado_conversacion = "solicitando_observaciones"
            conversation.set_context(context)
            self.db.commit()
            await self.sender.enviar_mensaje_botones(phone, "Observaciones", "¿Quieres agregar una observación?", [{"id": "sin_observaciones", "title": "No"}, {"id": "agregar_observacion", "title": "Sí, agregar"}])
            return
        if conversation.estado_conversacion == "solicitando_observaciones":
            if normalized in {"no", "sin observaciones", "sin_observaciones", "1"}:
                context["observaciones"] = ""
                await self._confirm(phone, conversation, context)
            else:
                conversation.estado_conversacion = "confirmando_observacion"
                self.db.commit()
                await self._text(phone, "Escribe la observación y luego te mostraré el resumen.")
            return
        if conversation.estado_conversacion == "confirmando_observacion":
            context["observaciones"] = text[:1000]
            await self._confirm(phone, conversation, context)
            return
        if conversation.estado_conversacion == "confirmando":
            if self._is_yes(text):
                await self._create_request(phone, conversation, context, text)
            elif normalized in {"corregir", "correction"}:
                conversation.estado_conversacion = "solicitando_flujo"
                conversation.set_context({"consentimiento_datos": True, "consentimiento_whatsapp": True})
                self.db.commit()
                await self._text(phone, "Claro. Empecemos de nuevo: indica si necesitas orgánicos o reciclables.")
            elif self._is_no(text):
                conversation.set_context({})
                conversation.estado_conversacion = "menu"
                draft = self.db.query(WhatsAppBorrador).filter(WhatsAppBorrador.telefono == phone).first()
                if draft:
                    self.db.delete(draft)
                self.db.commit()
                await self._text(phone, "Solicitud cancelada. No se creó ninguna recolección.")
                await self._menu(phone, conversation)
            else:
                await self._text(phone, "Responde *confirmar*, *corregir* o *cancelar*.")
            return

        await self._menu(phone, conversation)

    async def _confirm(self, phone: str, conversation: WhatsAppConversacion, context: dict) -> None:
        conversation.estado_conversacion = "confirmando"
        conversation.set_context(context)
        self.db.commit()
        flow = "orgánicos" if context.get("tipo_residuo") == "organico" else "reciclables"
        message = (f"Confirma tu solicitud:\n\nNombre: {context.get('nombre')}\n"
                   f"Generador: {context.get('tipo_generador')}\nFlujo: {flow}\n"
                   f"Dirección: {context.get('direccion')}\nDisponibilidad: {context.get('horario')}\n"
                   f"Observaciones: {context.get('observaciones') or 'Ninguna'}")
        await self.sender.enviar_mensaje_botones(phone, "Confirmar solicitud", message, [{"id": "confirmar", "title": "Confirmar"}, {"id": "corregir", "title": "Corregir"}, {"id": "cancelar", "title": "Cancelar"}])

    async def _create_request(self, phone: str, conversation: WhatsAppConversacion, context: dict, original_text: str) -> None:
        if not context.get("consentimiento_datos") or not context.get("consentimiento_whatsapp"):
            conversation.estado_conversacion = "esperando_consentimiento"
            self.db.commit()
            await self._text(phone, "Necesito tu autorización antes de crear la solicitud. Responde *acepto*.")
            return
        tipo = TipoResiduo(context["tipo_residuo"])
        existing = self.db.query(Usuario).filter(Usuario.whatsapp == phone).first()
        if not existing:
            existing = Usuario(whatsapp=phone, nombre=context["nombre"], tipo_generador=TipoGenerador(context["tipo_generador"]), direccion=context["direccion"], barrio="Villas de San Pablo")
            self.db.add(existing)
            self.db.flush()
        else:
            existing.nombre = context["nombre"]
            existing.tipo_generador = TipoGenerador(context["tipo_generador"])
            existing.direccion = context["direccion"]
        existing.consentimiento_datos = True
        existing.consentimiento_whatsapp = True
        existing.consentimiento_en = datetime.now(timezone.utc)
        open_states = [EstadoSolicitud.RECIBIDA, EstadoSolicitud.EN_REVISION, EstadoSolicitud.ASIGNADA, EstadoSolicitud.PROGRAMADA]
        duplicate = self.db.query(Solicitud).filter(Solicitud.usuario_id == existing.id, Solicitud.tipo_residuo == tipo, Solicitud.estado.in_(open_states)).first()
        if duplicate:
            conversation.set_context({})
            conversation.estado_conversacion = "menu"
            self.db.commit()
            await self._text(phone, f"Ya tienes abierta la solicitud {duplicate.codigo_unico} para este flujo. Escribe *consultar* para ver su estado.")
            return
        solicitud = Solicitud(usuario_id=existing.id, tipo_residuo=tipo, estado=EstadoSolicitud.RECIBIDA, direccion=context["direccion"], disponibilidad_horaria=context["horario"], observaciones=context.get("observaciones"), mensaje_original=context.get("mensaje_original") or original_text, consentimiento_datos=True, consentimiento_whatsapp=True)
        self.db.add(solicitud)
        self.db.flush()
        self.db.add(HistorialEstado(solicitud_id=solicitud.id, estado_nuevo=solicitud.estado.value, observacion="Solicitud confirmada por el ciudadano vía WhatsApp"))
        colectivo_tipo = TipoColectivo.HUERTEROS if tipo == TipoResiduo.ORGANICO else TipoColectivo.RECICLADORES
        colectivo = self.db.query(Colectivo).filter(Colectivo.tipo == colectivo_tipo, Colectivo.activo == 1).first()
        self.db.commit()
        conversation.set_context({})
        conversation.estado_conversacion = "menu"
        draft = self.db.query(WhatsAppBorrador).filter(WhatsAppBorrador.telefono == phone).first()
        if draft:
            self.db.delete(draft)
        self.db.commit()
        tipo_label = "orgánicos" if tipo == TipoResiduo.ORGANICO else "reciclables"
        await self._text(phone, f"✅ Solicitud recibida: {solicitud.codigo_unico}\nFlujo: {tipo_label}\nLa revisará el coordinador correspondiente.")
        if colectivo and colectivo.whatsapp:
            await self._text(colectivo.whatsapp, f"📥 Nueva solicitud {solicitud.codigo_unico} de {tipo_label}. Revisa la bandeja del colectivo.")

    async def _send_requests(self, phone: str, user: Usuario | None) -> None:
        if not user:
            await self._text(phone, "No encuentro solicitudes asociadas a este número.")
            return
        states = [EstadoSolicitud.RECIBIDA, EstadoSolicitud.EN_REVISION, EstadoSolicitud.ASIGNADA, EstadoSolicitud.PROGRAMADA]
        requests = self.db.query(Solicitud).filter(Solicitud.usuario_id == user.id, Solicitud.estado.in_(states)).order_by(Solicitud.creado_en.desc()).limit(10).all()
        if not requests:
            await self._text(phone, "No tienes solicitudes activas.")
            return
        lines = ["Tus solicitudes activas:"]
        for item in requests:
            line = f"• {item.codigo_unico}: {item.estado.value} ({item.tipo_residuo.value})"
            assignment = self.db.query(Asignacion).filter(Asignacion.solicitud_id == item.id).order_by(Asignacion.creado_en.desc()).first()
            if assignment and assignment.fecha_programada:
                line += f" | {assignment.fecha_programada.strftime('%Y-%m-%d %H:%M')} | {assignment.persona_encargada}"
            lines.append(line)
        await self._text(phone, "\n".join(lines))

    async def _send_points(self, phone: str, user: Usuario | None) -> None:
        if not user:
            await self._text(phone, "Aún no tienes puntos registrados.")
            return
        movements = self.db.query(PuntuacionHistorial).filter(PuntuacionHistorial.usuario_id == user.id).order_by(PuntuacionHistorial.creado_en.desc()).limit(3).all()
        detail = "\n".join(f"• +{movement.puntos} puntos (movimiento {movement.id})" for movement in movements) or "Aún no hay movimientos."
        await self._text(phone, f"Tus puntos acumulados: {user.puntos or 0}.\n{detail}\n\nLos valores son configurables y están sujetos a validación de la Fundación Santo Domingo.")

