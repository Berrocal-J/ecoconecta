import re
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 10 and digits.startswith("3"):
        return "57" + digits
    return digits


class WhatsAppService:
    """Cliente de WhatsApp Cloud API sin registrar secretos ni contenido sensible."""

    def __init__(self):
        api_version = settings.WHATSAPP_API_VERSION or "v23.0"
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.timeout = httpx.Timeout(settings.WHATSAPP_GRAPH_TIMEOUT_SECONDS)

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                result = response.json()
                if response.is_error:
                    return {"success": False, "status_code": response.status_code, "error": result}
                return result
        except (httpx.HTTPError, ValueError) as error:
            return {"success": False, "error": {"type": error.__class__.__name__}}

    async def enviar_mensaje_texto(self, to: str, mensaje: str) -> Dict[str, Any]:
        return await self._post({
            "messaging_product": "whatsapp", "to": normalize_phone(to), "type": "text",
            "text": {"preview_url": False, "body": mensaje[:4096]},
        })

    async def enviar_mensaje_botones(self, to: str, titulo: str, cuerpo: str, botones: list[dict[str, str]]) -> Dict[str, Any]:
        return await self._post({
            "messaging_product": "whatsapp", "to": normalize_phone(to), "type": "interactive",
            "interactive": {
                "type": "button", "header": {"type": "text", "text": titulo[:60]},
                "body": {"text": cuerpo[:1024]},
                "action": {"buttons": [{"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}} for b in botones[:3]]},
            },
        })

    async def enviar_mensaje_lista(self, to: str, titulo: str, cuerpo: str, opciones: list[dict[str, str]]) -> Dict[str, Any]:
        return await self._post({
            "messaging_product": "whatsapp", "to": normalize_phone(to), "type": "interactive",
            "interactive": {
                "type": "list", "header": {"type": "text", "text": titulo[:60]},
                "body": {"text": cuerpo[:1024]},
                "action": {"button": "Ver opciones", "sections": [{"title": "EcoConecta", "rows": [{"id": o["id"], "title": o["title"][:24]} for o in opciones[:10]]}]},
            },
        })

    async def enviar_mensaje_template(self, to: str, template_name: str, components: list | None = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp", "to": normalize_phone(to), "type": "template",
            "template": {"name": template_name, "language": {"code": "es"}},
        }
        if components:
            payload["template"]["components"] = components
        return await self._post(payload)

    async def enviar_notificacion(self, to: str, mensaje: str, template_name: str = "", components: list | None = None) -> Dict[str, Any]:
        if template_name:
            return await self.enviar_mensaje_template(to, template_name, components)
        return await self.enviar_mensaje_texto(to, mensaje)

    async def descargar_audio(self, media_id: str) -> Optional[bytes]:
        if not media_id:
            return None
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                metadata = await client.get(f"{self.base_url}/{media_id}", headers=headers)
                if metadata.is_error:
                    return None
                media_url = metadata.json().get("url")
                if not media_url:
                    return None
                media = await client.get(media_url, headers=headers)
                return media.content if media.is_success else None
        except httpx.HTTPError:
            return None

    def verificar_webhook(self, mode: str, token: str) -> bool:
        return bool(settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN) and mode == "subscribe" and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN


class WhatsAppSimulator:
    def __init__(self):
        self.mensajes_enviados: list[dict[str, Any]] = []

    async def enviar_mensaje_texto(self, to: str, mensaje: str) -> Dict[str, Any]:
        return self._store(to, "text", {"body": mensaje})

    async def enviar_mensaje_botones(self, to: str, titulo: str, cuerpo: str, botones: list[dict[str, str]]) -> Dict[str, Any]:
        return self._store(to, "interactive", {"header": titulo, "body": cuerpo, "buttons": botones})

    async def enviar_mensaje_lista(self, to: str, titulo: str, cuerpo: str, opciones: list[dict[str, str]]) -> Dict[str, Any]:
        return self._store(to, "interactive", {"header": titulo, "body": cuerpo, "rows": opciones})

    async def enviar_mensaje_template(self, to: str, template_name: str, components: list | None = None) -> Dict[str, Any]:
        return self._store(to, "template", {"name": template_name, "components": components or []})

    async def enviar_notificacion(self, to: str, mensaje: str, template_name: str = "", components: list | None = None) -> Dict[str, Any]:
        if template_name:
            return await self.enviar_mensaje_template(to, template_name, components)
        return await self.enviar_mensaje_texto(to, mensaje)

    async def descargar_audio(self, media_id: str) -> Optional[bytes]:
        return None

    def _store(self, to: str, tipo: str, contenido: dict) -> Dict[str, Any]:
        message_id = f"sim_{len(self.mensajes_enviados) + 1}"
        self.mensajes_enviados.append({"to": normalize_phone(to), "tipo": tipo, "contenido": contenido, "timestamp": "simulado"})
        return {"success": True, "message_id": message_id}

    def get_mensajes_enviados(self) -> list:
        return self.mensajes_enviados

    def clear_mensajes(self):
        self.mensajes_enviados.clear()


whatsapp_service = WhatsAppService() if settings.USE_EXTERNAL_SERVICES and settings.WHATSAPP_ACCESS_TOKEN else WhatsAppSimulator()
