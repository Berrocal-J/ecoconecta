# IA responsable

La IA es auxiliar, no toma decisiones operativas.

- Audio: OpenAI Whisper mediante `OPENAI_TRANSCRIPTION_MODEL`.
- Extracción: modelo configurable por `OPENAI_MODEL`; la salida se valida con Pydantic.
- Si falla OpenAI, el flujo guiado por texto, botones y listas sigue funcionando.
- Antes de extraer, se enmascaran teléfonos y nombres identificables.
- El usuario confirma el resumen antes de crear una solicitud.
- Asignación, horario confirmado, cierre y puntos quedan bajo control humano.

Variables: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TRANSCRIPTION_MODEL`.

La integración real con OpenAI y audio de Meta requiere credenciales y prueba externa; el simulador local usa una transcripción ficticia controlada.
