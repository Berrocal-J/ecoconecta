# Matriz de seguridad

| Zona | Rol | Protección |
|---|---|---|
| Login | público con rate limit PostgreSQL | JWT solo para cuentas activas |
| Solicitud pública y consulta con token | ciudadano | solo datos mínimos y token privado |
| Bandeja huerteros | `COORD_HUERTEROS`, `ADMIN` | filtro obligatorio por flujo orgánico |
| Bandeja recicladores | `COORD_RECICLADORES`, `ADMIN` | filtro obligatorio por flujo reciclable |
| Programar/cerrar/cancelar | coordinador de su flujo, `ADMIN` | validación de flujo y estado |
| Usuarios y datos de contacto | `ADMIN` | no hay endpoint público administrativo |
| Colectivos, reglas y contenidos | `ADMIN` para cambios | lectura operativa acotada al colectivo |
| Pilotos y solicitudes de eliminación | `ADMIN` | gestión administrativa |
| Webhook | Meta | verify token + HMAC cuando App Secret está configurado |
| Simulador | desarrollo | deshabilitado cuando `USE_EXTERNAL_SERVICES=true` |

Los payloads de eventos no se exponen por API. Debe aplicarse retención operativa con `DATA_RETENTION_DAYS` antes del despliegue productivo. Las contraseñas se almacenan como PBKDF2 y las claves se cargan desde entorno.
Los recolectores autenticados usan los roles `HUERTERO` y `RECICLADOR` y solo consultan sus asignaciones propias en `/recolectores/mis-asignaciones`. El contacto y la dirección se entregan únicamente para esas asignaciones.
