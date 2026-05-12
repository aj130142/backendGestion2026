# Documentación Técnica: Sistema de Gestión TechSolutions (Backend)

## 1. Resumen Ejecutivo
El Backend de TechSolutions es una API RESTful de alto rendimiento diseñada para orquestar flujos de trabajo de gestión de proyectos y asignación de recursos. Construido sobre un stack asíncrono moderno, proporciona un entorno seguro para la persistencia de datos, control de acceso basado en roles (RBAC) y agregación analítica en tiempo real.

## 2. Arquitectura del Sistema

### 2.1 Diseño por Capas
El sistema sigue una estricta separación de responsabilidades para garantizar el mantenimiento y la escalabilidad:
- **Capa de Presentación (Routers)**: Define los endpoints HTTP y gestiona el ciclo de vida de las solicitudes/respuestas.
- **Capa de Lógica de Negocio (Services)**: Implementa reglas específicas del dominio, como la validación de fechas y el aprovisionamiento automático de cuentas.
- **Capa de Acceso a Datos (Models)**: Gestiona las interacciones con la base de datos utilizando el ORM SQLAlchemy con un controlador asíncrono (`asyncpg`).
- **Capa de Validación (Schemas)**: Utiliza Pydantic para la comprobación estricta de tipos y la serialización/deserialización de datos.

### 2.2 Paradigma Asíncrono
El motor central utiliza la librería `asyncio` de Python. Todas las operaciones de base de datos, firma de tokens y tareas de E/S son no bloqueantes, lo que permite al sistema manejar un alto volumen de solicitudes concurrentes con una sobrecarga mínima de recursos.

### 2.3 Jerarquía de Directorios
El proyecto sigue una estructura modular para separar responsabilidades:

```text
backend/
├── app/
│   ├── auth/           # Lógica de autenticación y dependencias JWT
│   ├── models/         # Modelos de base de datos SQLAlchemy (3NF)
│   ├── routers/        # Endpoints de API agrupados por módulo (Clientes, Proyectos, etc.)
│   ├── schemas/        # Esquemas Pydantic para validación de datos
│   ├── config.py       # Variables de entorno y configuración del sistema
│   ├── database.py     # Motor de base de datos y gestión de sesiones
│   ├── main.py         # Punto de entrada de la aplicación y middlewares
│   └── limiter.py      # Lógica de limitación de tasa (Rate limiting)
├── requirements.txt    # Dependencias del proyecto
├── seed.sql            # Inicialización de base de datos y registros base
└── .env                # Configuración de variables sensibles
```

## 3. Módulos Funcionales Principales

### 3.1 Gestión de Identidad y Acceso (IAM)
- **Autenticación**: Implementación de OAuth2 con flujo de contraseña. Los tokens JWT incluyen claims de seguridad (Emisor, Audiencia, JTI).
- **Autorización (RBAC)**: Matriz dinámica de permisos. El acceso se evalúa por módulo (Clientes, Proyectos, Tareas, Usuarios) y por operación (Crear, Leer, Actualizar, Eliminar).
- **Seguridad de Tokens**: Lista de revocación (Blacklist) para invalidar sesiones al cerrar sesión.

### 3.2 Gestión de Clientes y Proyectos
- **Módulo de Clientes**: Gestiona la información de empresas y contactos. Incluye un disparador lógico que crea automáticamente una cuenta de usuario cuando se registra un nuevo cliente.
- **Módulo de Proyectos**: Controla el ciclo de vida (Pendiente, En Progreso, Completado). Permite la vinculación de múltiples usuarios internos a un proyecto específico.

### 3.3 Sistema de Seguimiento de Tareas
- **Validación de Línea de Tiempo**: Reglas de negocio que impiden que las fechas de las tareas caigan fuera del rango del proyecto padre.
- **Gestión de Estados**: Registro histórico de transiciones de estado para auditoría y análisis de rendimiento.
- **Priorización**: Clasificación granular (Alta, Media, Baja) para la gestión de urgencias.

### 3.4 Análisis y Reportes
- **Motor Analítico**: Endpoints dedicados para el cálculo de estadísticas en tiempo real (distribución de estados por proyecto).
- **Soporte de Documentación**: Preparación de estructuras de datos para la generación de reportes PDF con visualizaciones gráficas.

## 4. Especificaciones Técnicas

### 4.1 Persistencia de Datos
- **Base de Datos Relacional**: Diseño normalizado (3NF) para garantizar la integridad.
- **Restricciones de Integridad**: Uso estricto de claves foráneas y eliminaciones en cascada controladas.

### 4.2 Protocolos de Seguridad
- **Cifrado de Credenciales**: Las contraseñas se procesan mediante BCrypt con un factor de trabajo de 12.
- **Saneamiento de Entradas**: Los esquemas Pydantic previenen inyecciones SQL y ataques XSS mediante validación estricta de tipos.

## 5. Guía de Operación

### 5.1 Configuración Inicial
1. **Entorno**: Python 3.10+, PostgreSQL 13+.
2. **Dependencias**: `pip install -r requirements.txt`.
3. **Base de Datos**: Ejecutar `seed.sql` para inicializar roles y permisos.

### 5.2 Interacción con la API
- **Swagger UI**: `/docs` (Interfaz interactiva para pruebas).
- **ReDoc**: `/redoc` (Documentación técnica estructurada).
