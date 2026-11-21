from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_current_account, hash_password
from app.models.cuenta_acceso import CuentaAcceso
from app.models.conversacion import LoginIntento
from app.core.config import settings
from app.schemas.auth import LoginRequest, LoginResponse, CuentaActual, ChangePasswordRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    since = datetime.now(timezone.utc) - timedelta(minutes=1)
    attempts = db.query(LoginIntento).filter(LoginIntento.ip == ip, LoginIntento.creado_en >= since).count()
    if attempts >= settings.AUTH_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Intenta de nuevo en un minuto")
    account = db.query(CuentaAcceso).filter(CuentaAcceso.usuario == data.usuario, CuentaAcceso.activo.is_(True)).first()
    if not account or not verify_password(data.password, account.password_hash):
        db.add(LoginIntento(usuario=data.usuario[:80], ip=ip[:80], exitoso=False))
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o password invalidos")
    db.add(LoginIntento(usuario=data.usuario[:80], ip=ip[:80], exitoso=True))
    db.commit()
    return LoginResponse(access_token=create_access_token(account), usuario=account.usuario, nombre=account.nombre, rol=account.rol.value)


@router.get("/me", response_model=CuentaActual)
def me(account: CuentaAcceso = Depends(get_current_account)):
    return CuentaActual(usuario=account.usuario, nombre=account.nombre, rol=account.rol.value)


@router.post("/cambiar-password")
def cambiar_password(data: ChangePasswordRequest, db: Session = Depends(get_db), account: CuentaAcceso = Depends(get_current_account)):
    if not verify_password(data.actual, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual no es válida")
    if data.actual == data.nueva:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente")
    account.password_hash = hash_password(data.nueva)
    db.commit()
    return {"success": True, "mensaje": "Contraseña actualizada"}
