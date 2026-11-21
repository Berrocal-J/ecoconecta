from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.routers import usuarios, solicitudes, colectivos, asignaciones, recolecciones, puntuacion, whatsapp, auth, contenidos, pilotos, recolectores

app = FastAPI(
    title="EcoConecta API",
    description="API para gestión de residuos en Villas de San Pablo",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(usuarios.router)
app.include_router(solicitudes.router)
app.include_router(colectivos.router)
app.include_router(asignaciones.router)
app.include_router(recolecciones.router)
app.include_router(puntuacion.router)
app.include_router(whatsapp.router)
app.include_router(auth.router)
app.include_router(contenidos.router)
app.include_router(pilotos.router)
app.include_router(recolectores.router)


@app.get("/")
def root():
    return {
        "mensaje": "EcoConecta API - Villas de San Pablo",
        "version": "1.0.0",
        "documentacion": "/docs"
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "ok"}
