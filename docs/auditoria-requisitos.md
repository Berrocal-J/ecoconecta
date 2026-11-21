# Auditoría de requisitos EcoConecta

Fecha de revisión: 20 de noviembre de 2026.

| Requisito | Estado actual | Evidencia o pendiente |
|---|---|---|
| PostgreSQL, FastAPI, SQLAlchemy, Next.js y Docker | Implementado | Compose, Alembic y build Next.js preparados. Validación final depende de Docker Desktop activo. |
| RN-01 separación y enrutamiento por flujo | Implementado | Conversación y panel separan orgánicos/huerteros de reciclables/recicladores. |
| RN-02 programación completa | Implementado | Fecha, hora y recolector son obligatorios para programar. |
| RN-03 asignación auditable | Implementado | `recolectores`, `recolector_id`, colectivo e historial de asignaciones. |
| RN-04 estados e historial | Implementado | `estado_service.py` rechaza retrocesos y registra transiciones/cancelaciones. |
| RN-05 puntos después del cierre | Implementado | Cierre calcula puntos una sola vez y registra historial explicable. |
| RN-06 reglas parametrizables | Implementado | Reglas y bonos viven en PostgreSQL; valores son de ejemplo y requieren validación FSD. |
| RN-07 seguridad y privacidad | Implementado parcialmente | JWT, roles, aislamiento de flujos, HMAC y consultas ciudadanas con token. Falta ejecutar pruebas API completas con Docker. |
| RN-08 usuarios piloto | Implementado | Tabla `usuarios_piloto`, modo piloto y CRUD ADMIN. |
| Conversación WhatsApp persistente | Implementado | Estado y contexto en PostgreSQL; borradores explícitos en `whatsapp_borradores`; TTL configurable. |
| Webhook Cloud API | Implementado | Firma HMAC, múltiples entries/changes/messages, idempotencia, audio y estados de entrega. Pendiente prueba con Meta real. |
| Cola saliente y reintentos | Implementado | Registro persistente y endpoint ADMIN `/whatsapp/cola/reintentar` con backoff limitado. Falta instalar scheduler de producción. |
| Panel coordinador | Implementado | Bandejas, programación, recolector, cierre y resumen por flujo. |
| Panel recolector | Implementado | `/recolector` y `/recolectores/mis-asignaciones`, limitado a sus propias asignaciones. |
| Admin | Parcial | Gestión de datos operativos, pilotos, contenido y reglas. CRUD avanzado de cuentas/auditoría administrativa requiere ampliación. |
| IA responsable | Implementado | Modelos configurables, validación Pydantic y enmascaramiento; audio real pendiente de credenciales. |
| Despliegue productivo | Pendiente externo | HTTPS, proveedor cloud, dominio, backups, secretos Meta y plantillas aprobadas. |

No se declaran probados los puntos que requieren cuenta Meta, número real, OpenAI o infraestructura pública.
