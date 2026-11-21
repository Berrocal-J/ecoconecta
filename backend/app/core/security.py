from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.cuenta_acceso import CuentaAcceso, RolAcceso

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return "pbkdf2_sha256$120000$" + salt.hex() + "$" + digest.hex()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        candidate = hashlib.pbkdf2_hmac(algorithm.removeprefix("pbkdf2_"), password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(account: CuentaAcceso) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(account.id), "usuario": account.usuario, "rol": account.rol.value, "exp": expires}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_account(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> CuentaAcceso:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion requerida")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        account_id = int(payload.get("sub", ""))
    except (JWTError, ValueError, TypeError):
        raise credentials_error
    account = db.query(CuentaAcceso).filter(CuentaAcceso.id == account_id, CuentaAcceso.activo.is_(True)).first()
    if not account:
        raise credentials_error
    return account


def require_roles(*roles: RolAcceso):
    def dependency(account: CuentaAcceso = Depends(get_current_account)) -> CuentaAcceso:
        if account.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta zona")
        return account
    return dependency
