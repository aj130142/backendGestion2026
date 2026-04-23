from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ─── AUTH ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    correo: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── ROLES ───────────────────────────────────────────────────────────────────

class RolBase(BaseModel):
    nombre_rol: str

class RolOut(RolBase):
    id_rol: int
    class Config:
        from_attributes = True


# ─── USUARIOS ────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    password: str
    id_rol: int

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    password: Optional[str] = None
    id_rol: Optional[int] = None
    activo: Optional[bool] = None

class UsuarioOut(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    id_rol: int
    activo: bool
    creado_en: Optional[datetime] = None
    rol: Optional[RolOut] = None
    class Config:
        from_attributes = True


# ─── ESTADOS ─────────────────────────────────────────────────────────────────

class EstadoOut(BaseModel):
    id_estado: int
    entidad: str
    nombre: str
    class Config:
        from_attributes = True


# ─── CLIENTES ────────────────────────────────────────────────────────────────

class ClienteCreate(BaseModel):
    nombre: str
    correo: Optional[str] = None
    telefono: Optional[str] = None
    empresa: Optional[str] = None
    id_estado: int

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    empresa: Optional[str] = None
    id_estado: Optional[int] = None

class ClienteOut(BaseModel):
    id_cliente: int
    nombre: str
    correo: Optional[str] = None
    telefono: Optional[str] = None
    empresa: Optional[str] = None
    id_estado: int
    creado_en: Optional[datetime] = None
    estado: Optional[EstadoOut] = None
    class Config:
        from_attributes = True


# ─── PROYECTOS ───────────────────────────────────────────────────────────────

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    id_cliente: int
    id_estado: int

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    id_cliente: Optional[int] = None
    id_estado: Optional[int] = None

class ProyectoOut(BaseModel):
    id_proyecto: int
    nombre: str
    descripcion: Optional[str] = None
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    id_cliente: int
    id_estado: int
    creado_en: Optional[datetime] = None
    estado: Optional[EstadoOut] = None
    cliente: Optional[ClienteOut] = None
    class Config:
        from_attributes = True

class AsignarUsuariosRequest(BaseModel):
    id_usuarios: list[int]


# ─── PRIORIDADES ─────────────────────────────────────────────────────────────

class PrioridadOut(BaseModel):
    id_prioridad: int
    nombre: str
    class Config:
        from_attributes = True


# ─── TAREAS ──────────────────────────────────────────────────────────────────

class TareaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    id_proyecto: int
    id_prioridad: int
    id_estado: int
    fecha_inicio: date
    fecha_fin: Optional[date] = None

class TareaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    id_proyecto: Optional[int] = None
    id_prioridad: Optional[int] = None
    id_estado: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

class TareaUsuarioOut(BaseModel):
    id_usuario: int
    usuario: Optional[UsuarioOut] = None
    class Config:
        from_attributes = True

class TareaOut(BaseModel):
    id_tarea: int
    nombre: str
    descripcion: Optional[str] = None
    id_proyecto: int
    id_prioridad: int
    id_estado: int
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    creado_en: Optional[datetime] = None
    estado: Optional[EstadoOut] = None
    prioridad: Optional[PrioridadOut] = None
    usuarios: list[TareaUsuarioOut] = []

    class Config:
        from_attributes = True


# ─── HISTORIAL ───────────────────────────────────────────────────────────────

class HistorialOut(BaseModel):
    id_historial: int
    entidad: str
    id_entidad: int
    id_estado_ant: Optional[int] = None
    id_estado_nuevo: int
    id_usuario: int
    cambiado_en: Optional[datetime] = None
    estado_ant: Optional[EstadoOut] = None
    estado_nuevo: Optional[EstadoOut] = None
    class Config:
        from_attributes = True


# ─── MÓDULOS ─────────────────────────────────────────────────────────────────

class ModuloOut(BaseModel):
    id_modulo: int
    nombre: str
    class Config:
        from_attributes = True


# ─── PERMISOS ────────────────────────────────────────────────────────────────

class RolPermisoBase(BaseModel):
    id_rol: int
    id_modulo: int
    puede_ver: bool = False
    puede_crear: bool = False
    puede_editar: bool = False
    puede_eliminar: bool = False

class RolPermisoOut(RolPermisoBase):
    modulo: Optional[ModuloOut] = None
    class Config:
        from_attributes = True
