from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario: str
    password: str


class ChangePasswordRequest(BaseModel):
    actual: str = Field(..., min_length=8)
    nueva: str = Field(..., min_length=12)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: str
    nombre: str
    rol: str


class CuentaActual(BaseModel):
    usuario: str
    nombre: str
    rol: str
