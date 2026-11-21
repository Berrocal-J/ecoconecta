"""Comprueba la conexión con WhatsApp Cloud API leyendo el .env.

Uso:
  python scripts/verificar_whatsapp.py                 # valida token y Phone Number ID
  python scripts/verificar_whatsapp.py 573001234567    # además envía la plantilla hello_world
"""
import os, sys, json
import httpx

def load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
version = os.getenv("WHATSAPP_API_VERSION", "v23.0")
base = f"https://graph.facebook.com/{version}"

def check(name, ok, hint=""):
    print(("[OK]   " if ok else "[FALTA]"), name, "" if ok else f"-> {hint}")
    return ok

ok = True
ok &= check("USE_EXTERNAL_SERVICES=true", os.getenv("USE_EXTERNAL_SERVICES", "").lower() == "true", "ponlo en true")
ok &= check("WHATSAPP_PHONE_NUMBER_ID", bool(phone_id), "cópialo de API Setup")
ok &= check("WHATSAPP_ACCESS_TOKEN", bool(token), "genera el token en API Setup")
ok &= check("WHATSAPP_APP_SECRET", bool(os.getenv("WHATSAPP_APP_SECRET")), "Configuración de la app > Básica")
ok &= check("WHATSAPP_WEBHOOK_VERIFY_TOKEN", bool(os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")), "inventa una frase larga")
if not (phone_id and token):
    sys.exit(1)

h = {"Authorization": f"Bearer {token}"}
r = httpx.get(f"{base}/{phone_id}", headers=h, params={"fields": "display_phone_number,verified_name,quality_rating"}, timeout=20)
if r.is_success:
    print("[OK]   Token y Phone Number ID válidos:", json.dumps(r.json(), ensure_ascii=False))
else:
    err = r.json().get("error", {})
    print("[ERROR] Graph API:", err.get("code"), err.get("message"))
    if err.get("code") == 190:
        print("        El token venció (dura ~24 h). Genera uno nuevo en API Setup.")
    sys.exit(1)

if len(sys.argv) > 1:
    to = sys.argv[1]
    payload = {"messaging_product": "whatsapp", "to": to, "type": "template",
               "template": {"name": "hello_world", "language": {"code": "en_US"}}}
    r = httpx.post(f"{base}/{phone_id}/messages", headers=h, json=payload, timeout=20)
    print("[OK]   hello_world enviado" if r.is_success else f"[ERROR] {r.text[:300]}")
    if r.status_code == 400 and "131030" in r.text:
        print("        Ese número no está en la lista de destinatarios de prueba.")
sys.exit(0 if ok else 1)
