# Estado final del MVP

## Implementado y probado localmente

- FastAPI + SQLAlchemy + PostgreSQL + Alembic + Next.js + Docker.
- JWT, PBKDF2, roles de administrador y coordinadores con aislamiento de flujos.
- Conversación WhatsApp persistente en PostgreSQL, consentimiento, menú, botones/listas, confirmación y cancelación.
- Solicitudes orgánicas y reciclables enrutadas a su colectivo.
- Programación con fecha, hora, recolector/persona y trazabilidad.
- Cierre con material, peso, cualidades y puntos explicables.
- Webhook HMAC, idempotencia por mensaje, payloads con múltiples entries/changes/messages y estados de entrega.
- Simulador local de texto, interactivos y audio ficticio.
- Rate limit de login y de mensajes entrantes.
- Contenido educativo, modo piloto y solicitudes de eliminación de datos en PostgreSQL.

## Simulado o pendiente de prueba externa

- Entrega real de mensajes por Meta Cloud API: requiere App, número, token, App Secret y URL HTTPS.
- Audio real de WhatsApp + Whisper: requiere token Meta, `OPENAI_API_KEY` y prueba de media.
- Plantillas aprobadas y comportamiento fuera de la ventana de atención de Meta.
- Despliegue nube, dominio, HTTPS, backups y restauración.

## Limitaciones conocidas

- La vista de recolector autenticado y la gestión CRUD completa de cuentas/colectivos requieren una iteración adicional de frontend.
- La cola saliente registra el intento y estado; el worker de reintentos con backoff debe ejecutarse como proceso de producción.
- La política de retención de payloads debe automatizarse en el proveedor PostgreSQL.
- Horarios, rutas y puntos son configurables y no representan reglas oficiales hasta validación de la Fundación Santo Domingo.

## Últimos ajustes

- Migración `0008_collector_roles` con roles autenticados `HUERTERO` y `RECICLADOR`.
- Panel privado de asignaciones propias en `/recolector` y endpoint protegido para el recolector.
- `GET /solicitudes/resumen`, acotado por flujo para coordinadores y global para admin.
- `POST /whatsapp/cola/reintentar`, exclusivo de ADMIN, con backoff acotado y máximo configurable.
- El cierre estándar de recolección calcula puntos y notifica al ciudadano respetando consentimiento.

## Comandos verificados

Nota: la vista del recolector y la cola de reintentos descritas en los ajustes ya estÃ¡n implementadas en el estado actual del cÃ³digo; queda pendiente Ãºnicamente ejecutar la validaciÃ³n dentro de Docker cuando el daemon estÃ© disponible.

```powershell
docker compose up --build -d
docker compose exec -T backend alembic upgrade head
docker compose exec -T backend python -m compileall -q /app/app /app/seeds/seed_data.py
```

La prueba conversacional local confirmó la creación de una solicitud orgánica después de consentimiento y confirmación, su llegada a huerteros y la notificación simulada al colectivo.
