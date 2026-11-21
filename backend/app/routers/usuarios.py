from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.core.security import require_roles
from app.models.cuenta_acceso import RolAcceso
from app.models.conversacion import SolicitudEliminacion

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/solicitudes-eliminacion")
def listar_solicitudes_eliminacion(db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    return db.query(SolicitudEliminacion).order_by(SolicitudEliminacion.creado_en.desc()).all()


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    db_usuario = db.query(Usuario).filter(Usuario.whatsapp == usuario.whatsapp).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="Usuario ya existe con este WhatsApp")

    nuevo_usuario = Usuario(**usuario.model_dump())
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.get("/whatsapp/{whatsapp}", response_model=UsuarioResponse)
def obtener_usuario_por_whatsapp(whatsapp: str, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    usuario = db.query(Usuario).filter(Usuario.whatsapp == whatsapp).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = usuario.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_usuario, key, value)

    db.commit()
    db.refresh(db_usuario)
    return db_usuario
