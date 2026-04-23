from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Date, ForeignKey, Integer, String,
    Text, TIMESTAMP, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), nullable=False, unique=True)

    usuarios = relationship("Usuario", back_populates="rol")
    permisos = relationship("RolPermiso", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    activo = Column(Boolean, default=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    rol = relationship("Rol", back_populates="usuarios")
    tokens_revocados = relationship("TokenRevocado", back_populates="usuario", cascade="all, delete-orphan")
    proyectos = relationship("ProyectoUsuario", back_populates="usuario", cascade="all, delete-orphan")
    tareas = relationship("TareaUsuario", back_populates="usuario", cascade="all, delete-orphan")
    historial = relationship("HistorialEstado", back_populates="usuario", cascade="all, delete-orphan")


class TokenRevocado(Base):
    __tablename__ = "tokens_revocados"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(Text, nullable=False, unique=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    revocado_en = Column(TIMESTAMP, server_default=func.now())

    usuario = relationship("Usuario", back_populates="tokens_revocados")


class Estado(Base):
    __tablename__ = "estados"

    id_estado = Column(Integer, primary_key=True, index=True)
    entidad = Column(String(50), nullable=False)
    nombre = Column(String(50), nullable=False)

    __table_args__ = (UniqueConstraint("entidad", "nombre"),)

    clientes = relationship("Cliente", back_populates="estado")
    proyectos = relationship("Proyecto", back_populates="estado")
    tareas = relationship("Tarea", back_populates="estado")


class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True)
    telefono = Column(String(20))
    empresa = Column(String(100))
    id_estado = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    estado = relationship("Estado", back_populates="clientes")
    proyectos = relationship("Proyecto", back_populates="cliente")


class Proyecto(Base):
    __tablename__ = "proyectos"

    id_proyecto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    id_estado = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    cliente = relationship("Cliente", back_populates="proyectos")
    estado = relationship("Estado", back_populates="proyectos")
    usuarios = relationship("ProyectoUsuario", back_populates="proyecto")
    tareas = relationship("Tarea", back_populates="proyecto")


class ProyectoUsuario(Base):
    __tablename__ = "proyecto_usuarios"

    id_proyecto = Column(Integer, ForeignKey("proyectos.id_proyecto"), primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    asignado_en = Column(TIMESTAMP, server_default=func.now())

    proyecto = relationship("Proyecto", back_populates="usuarios")
    usuario = relationship("Usuario", back_populates="proyectos")


class Prioridad(Base):
    __tablename__ = "prioridades"

    id_prioridad = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)

    tareas = relationship("Tarea", back_populates="prioridad")


class Tarea(Base):
    __tablename__ = "tareas"

    id_tarea = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    id_proyecto = Column(Integer, ForeignKey("proyectos.id_proyecto"), nullable=False)
    id_prioridad = Column(Integer, ForeignKey("prioridades.id_prioridad"), nullable=False)
    id_estado = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    proyecto = relationship("Proyecto", back_populates="tareas")
    prioridad = relationship("Prioridad", back_populates="tareas")
    estado = relationship("Estado", back_populates="tareas")
    usuarios = relationship("TareaUsuario", back_populates="tarea")


class TareaUsuario(Base):
    __tablename__ = "tarea_usuarios"

    id_tarea = Column(Integer, ForeignKey("tareas.id_tarea"), primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    asignado_en = Column(TIMESTAMP, server_default=func.now())

    tarea = relationship("Tarea", back_populates="usuarios")
    usuario = relationship("Usuario", back_populates="tareas")


class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id_historial = Column(Integer, primary_key=True, index=True)
    entidad = Column(String(50), nullable=False)
    id_entidad = Column(Integer, nullable=False)
    id_estado_ant = Column(Integer, ForeignKey("estados.id_estado"))
    id_estado_nuevo = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    cambiado_en = Column(TIMESTAMP, server_default=func.now())

    usuario = relationship("Usuario", back_populates="historial")
    estado_ant = relationship("Estado", foreign_keys=[id_estado_ant])
    estado_nuevo = relationship("Estado", foreign_keys=[id_estado_nuevo])


class Modulo(Base):
    __tablename__ = "modulos"

    id_modulo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)

    permisos = relationship("RolPermiso", back_populates="modulo")


class RolPermiso(Base):
    __tablename__ = "rol_permisos"

    id_rol = Column(Integer, ForeignKey("roles.id_rol"), primary_key=True)
    id_modulo = Column(Integer, ForeignKey("modulos.id_modulo"), primary_key=True)
    puede_ver = Column(Boolean, default=False)
    puede_crear = Column(Boolean, default=False)
    puede_editar = Column(Boolean, default=False)
    puede_eliminar = Column(Boolean, default=False)

    rol = relationship("Rol", back_populates="permisos")
    modulo = relationship("Modulo", back_populates="permisos")
