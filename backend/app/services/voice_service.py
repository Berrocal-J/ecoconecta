import io
import json
import re
import unicodedata
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings


class SolicitudExtraida(BaseModel):
    tipo_residuo: Optional[str] = Field(default=None, pattern="^(organico|reciclable)$")
    direccion: Optional[str] = Field(default=None, max_length=255)
    horario: Optional[str] = Field(default=None, max_length=100)
    observaciones: Optional[str] = Field(default=None, max_length=1000)


def _mask_personal_data(texto: str) -> str:
    texto = re.sub(r"\b(?:\+?57)?3\d{9}\b", "[telefono]", texto)
    return re.sub(r"\b(?:nombre|me llamo)\s*[:\-]?\s*[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,60}", "nombre: [persona]", texto, flags=re.IGNORECASE)


class VoiceService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def transcribir_audio(self, audio_bytes: bytes, formato: str = "m4a") -> Optional[str]:
        if not audio_bytes:
            return None
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"audio.{formato}"
            result = self.client.audio.transcriptions.create(
                model=settings.OPENAI_TRANSCRIPTION_MODEL,
                file=audio_file,
                language="es",
            )
            return result.text
        except Exception as error:
            print(f"Error de transcripcion de audio: {error.__class__.__name__}")
            return None

    def extraer_datos_solicitud(self, texto: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Devuelve SOLO JSON. Extrae tipo_residuo (organico o reciclable), direccion, horario y observaciones. Usa null si falta. No incluyas datos distintos a esos campos."},
                    {"role": "user", "content": _mask_personal_data(texto)},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content or "{}")
            return SolicitudExtraida.model_validate(data).model_dump()
        except (ValidationError, ValueError, TypeError, Exception) as error:
            print(f"Extraccion IA no disponible: {error.__class__.__name__}")
            return {"tipo_residuo": None, "direccion": None, "horario": None, "observaciones": texto[:1000]}


class VoiceSimulator:
    def transcribir_audio(self, audio_bytes: bytes, formato: str = "m4a") -> Optional[str]:
        return "Hola, necesito que recojan residuos organicos en la calle 45 # 23-10, puedo recibirlos manana en la manana"

    def extraer_datos_solicitud(self, texto: str) -> dict:
        normalized = "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")
        tipo = None
        if any(term in normalized for term in ("organico", "organicos", "comida", "poda", "cascara")):
            tipo = "organico"
        elif any(term in normalized for term in ("reciclable", "reciclables", "plastico", "carton", "vidrio", "metal", "papel")):
            tipo = "reciclable"
        address_match = re.search(r"(?:calle|carrera|cra\.?|cl\.?)\s+[^,.;]+", normalized)
        horario = "manana" if "manana" in normalized else "tarde" if "tarde" in normalized else None
        return SolicitudExtraida(
            tipo_residuo=tipo,
            direccion=address_match.group(0).strip() if address_match else None,
            horario=horario,
            observaciones=texto[:1000],
        ).model_dump()
