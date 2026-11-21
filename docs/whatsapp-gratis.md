# Conectar EcoConecta a WhatsApp gratis (WhatsApp Business Cloud API)

Costo: **$0**. Meta entrega un número de prueba gratuito que puede enviar/recibir
mensajes con hasta **5 números verificados** (suficiente para la demo del hackathon).
La API de WhatsApp Business Cloud es el canal autorizado por el reto.

## 1. Crear la app en Meta (una sola vez)
1. Entra a https://developers.facebook.com con tu cuenta de Facebook → **Mis apps → Crear app**.
2. Tipo de app: **Empresa (Business)**. Agrega el producto **WhatsApp**.
3. Ve a **WhatsApp → Configuración de la API (API Setup)**. Allí Meta ya creó un
   **número de prueba**. Copia:
   - **Phone number ID** → `WHATSAPP_PHONE_NUMBER_ID` (no es el teléfono, es un ID largo)
   - **Access token** temporal (dura ~24 h) → `WHATSAPP_ACCESS_TOKEN`
4. En el campo **Para (To)** → *Administrar lista de números* → agrega y verifica
   (código por WhatsApp) hasta 5 celulares: el tuyo, el del equipo y el de los jurados que quieras.
   Cada uno debe enviar primero un mensaje al número de prueba (o recibir `hello_world`) y **permitir** el chat.
5. **Configuración de la app → Básica → App Secret** (clave de 32 caracteres hex) → `WHATSAPP_APP_SECRET`.
   Es OBLIGATORIO: el backend rechaza webhooks sin firma válida cuando `USE_EXTERNAL_SERVICES=true`.

## 2. Variables de entorno (`.env`, nunca en Git)
```
USE_EXTERNAL_SERVICES=true
WHATSAPP_PHONE_NUMBER_ID=<id del número de prueba>
WHATSAPP_ACCESS_TOKEN=<token>
WHATSAPP_APP_SECRET=<app secret>
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<una frase larga inventada por ti>
WHATSAPP_API_VERSION=v23.0
```
Con `USE_EXTERNAL_SERVICES=false` el sistema usa el **simulador** (sin Meta).
`docker compose up -d --build backend` para aplicar los cambios.

## 3. Exponer el webhook con HTTPS
Meta exige una URL pública HTTPS.
- **Local (gratis):** `cloudflared tunnel --url http://localhost:8000` (o `ngrok http 8000`) → te da `https://xxxx.trycloudflare.com`.
- **Desplegado:** usa la URL HTTPS de tu servicio en la nube.

## 4. Registrar el webhook
**WhatsApp → Configuración → Webhook → Editar**
- URL de devolución de llamada: `https://TU-URL/whatsapp/webhook`
- Token de verificación: el mismo valor de `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- Verificar y guardar → luego **suscribirte al campo `messages`**.

## 5. Probar
Desde un celular verificado escribe **hola** o **menu** al número de prueba (en WhatsApp → Nuevo chat
con el número que muestra API Setup). El bot debe responder. Crea una solicitud y programa
la recolección desde el panel del coordinador: el usuario recibe la confirmación por WhatsApp.

## Límites del plan gratuito (decláralos en la sustentación)
- Solo 5 destinatarios verificados (error `#131030` si el número no está en la lista).
- El token temporal vence a las ~24 h: regenéralo en API Setup antes de la demo del 21 de nov.
  Para uno que no venza: Business Settings → Usuarios del sistema → crear token de usuario del sistema.
- Mensajes de texto libre solo dentro de las 24 h posteriores al último mensaje del usuario
  (error `131047`). Fuera de esa ventana se requiere una plantilla aprobada
  (`WHATSAPP_TEMPLATE_*`, sin variables en esta versión). Para la demo: haz que el usuario escriba primero.
- Para atender a toda la comunidad se necesita un número real + verificación de negocio (fuera del MVP).

## Errores frecuentes
| Síntoma | Causa |
|---|---|
| Webhook no verifica (403) | `WHATSAPP_WEBHOOK_VERIFY_TOKEN` distinto al de Meta, o URL con `/` extra |
| Mensajes entrantes llegan con 403 | `WHATSAPP_APP_SECRET` vacío o incorrecto (no uses el token de acceso) |
| `Invalid OAuth access token` | Token temporal vencido (24 h) |
| `#131030` | Destinatario no agregado a la lista de prueba |
| El bot no responde | `USE_EXTERNAL_SERVICES=false`, o no te suscribiste al campo `messages` |
| `Unsupported version` | Cambia `WHATSAPP_API_VERSION` por una versión vigente |
