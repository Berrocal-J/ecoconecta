# Integracion WhatsApp Business Cloud API

## Configuracion manual en Meta

1. Crear una app tipo Business en Meta for Developers y agregar WhatsApp.
2. En WhatsApp > API Setup copiar el `Phone number ID` y generar el token de prueba. Para producción usar un token de sistema con los permisos aprobados por Meta.
3. Agregar el teléfono de prueba como destinatario autorizado.
4. Publicar el backend con HTTPS y registrar `https://DOMINIO/whatsapp/webhook` como callback URL.
5. Usar exactamente el mismo valor de `WHATSAPP_WEBHOOK_VERIFY_TOKEN` en EcoConecta y en Meta.
6. Suscribir el campo `messages` y probar primero texto; después audio y estados de entrega.

Para desarrollo local se puede usar un túnel HTTPS temporal hacia `http://localhost:8000`; no se debe usar como URL definitiva.

La aplicación verifica `GET /whatsapp/webhook`, valida `X-Hub-Signature-256` en cada POST cuando existe `WHATSAPP_APP_SECRET`, procesa todos los mensajes del payload y guarda los intentos de salida en PostgreSQL. Los reintentos se ejecutan con `POST /whatsapp/cola/reintentar`, protegido para ADMIN, y pueden ser invocados por un scheduler externo.

Variables requeridas:

- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- `WHATSAPP_APP_SECRET`
- `WHATSAPP_API_VERSION`
- `USE_EXTERNAL_SERVICES=true`

Webhook:

- Verificacion: `GET /whatsapp/webhook`.
- Recepcion: `POST /whatsapp/webhook`.
- El POST valida `X-Hub-Signature-256` cuando el App Secret esta configurado.
- Cada `message_id` se guarda una sola vez en PostgreSQL.
- Datos incompletos quedan como borrador y el ciudadano recibe una pregunta.

La prueba real depende de registrar un webhook HTTPS en Meta. El simulador local solo valida el codigo y no representa una entrega externa exitosa.
