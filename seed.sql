-- =============================================
-- SEED INICIAL — TechSolutions S.A.
-- Ejecutar UNA sola vez después de crear las tablas
-- =============================================

-- Roles
INSERT INTO roles (nombre_rol) VALUES ('Administrador'), ('Usuario')
ON CONFLICT (nombre_rol) DO NOTHING;

-- Estados por entidad
INSERT INTO estados (entidad, nombre) VALUES
  ('cliente',   'Activo'),
  ('cliente',   'Inactivo'),
  ('proyecto',  'En progreso'),
  ('proyecto',  'Completado'),
  ('proyecto',  'Cancelado'),
  ('proyecto',  'Pendiente'),
  ('tarea',     'Pendiente'),
  ('tarea',     'En progreso'),
  ('tarea',     'Completada'),
  ('tarea',     'Cancelada')
ON CONFLICT (entidad, nombre) DO NOTHING;

-- Prioridades
INSERT INTO prioridades (nombre) VALUES ('Alta'), ('Media'), ('Baja')
ON CONFLICT (nombre) DO NOTHING;

-- Módulos
INSERT INTO modulos (nombre) VALUES ('clientes'), ('proyectos'), ('tareas'), ('usuarios')
ON CONFLICT (nombre) DO NOTHING;

-- Permisos: Administrador (id_rol=1) tiene acceso total a todo
INSERT INTO rol_permisos (id_rol, id_modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
SELECT 1, id_modulo, TRUE, TRUE, TRUE, TRUE FROM modulos
ON CONFLICT (id_rol, id_modulo) DO UPDATE SET
  puede_ver = TRUE, puede_crear = TRUE, puede_editar = TRUE, puede_eliminar = TRUE;

-- Permisos: Usuario (id_rol=2) puede ver/crear/editar clientes, proyectos, tareas; no gestiona usuarios
INSERT INTO rol_permisos (id_rol, id_modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
SELECT 2, id_modulo, TRUE, TRUE, TRUE, FALSE FROM modulos WHERE nombre IN ('clientes', 'proyectos', 'tareas')
ON CONFLICT (id_rol, id_modulo) DO UPDATE SET
  puede_ver = TRUE, puede_crear = TRUE, puede_editar = TRUE, puede_eliminar = FALSE;

-- Usuario (id_rol=2) NO puede ver/gestionar el módulo usuarios
INSERT INTO rol_permisos (id_rol, id_modulo, puede_ver, puede_crear, puede_editar, puede_eliminar)
SELECT 2, id_modulo, FALSE, FALSE, FALSE, FALSE FROM modulos WHERE nombre = 'usuarios'
ON CONFLICT (id_rol, id_modulo) DO UPDATE SET
  puede_ver = FALSE, puede_crear = FALSE, puede_editar = FALSE, puede_eliminar = FALSE;

-- Usuario administrador inicial (password: Admin1234!)
-- IMPORTANTE: Cambiar o eliminar en producción
INSERT INTO usuarios (nombre, correo, password_hash, id_rol)
VALUES (
  'Administrador',
  'admin@techsolutions.com',
  '$2b$12$Z0H7M51fJkP.0G2G5zX7lOPjOhV4qD1mO/O7Qc3f6oR68lR2R/VWG',  -- Admin1234!
  1
) ON CONFLICT (correo) DO NOTHING;
