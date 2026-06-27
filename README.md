# API de Procesamiento de Mediciones

Backend desarrollado con **FastAPI** para la gestión, procesamiento y extracción de datos de mediciones y reportes técnicos de laboratorio.

Este servicio expone endpoints para integrar los resultados de mediciones en el sistema principal, permitiendo validar, aprobar, estructurar y consultar los datos extraídos.

## 🚀 Tecnologías Principales

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Gestión de dependencias:** [uv](https://github.com/astral-sh/uv) 
* **Contenedores:** Docker & Docker Compose
* **Lenguaje:** Python 3.12+
* **Base de datos:** SQLite, SQLModel como ORM y Alembic para gestionar las migraciones.

---

## 🛠️ Requisitos Previos

Para ejecutar este proyecto necesitas tener instalado:
* [Docker](https://docs.docker.com/get-docker/) (Para despliegue en contenedores)
* [uv](https://docs.astral.sh/uv/getting-started/installation/) (Solo si se quiere ejecutar el proyecto localmente sin Docker, se recomienda Docker por la facilidad de installación y ejecución.)

---

## 🐳 Despliegue con Docker (Recomendado)

El proyecto incluye un `Dockerfile` optimizado (multistage) que instala las dependencias nativamente garantizando que no haya conflictos de rutas ni de sistema operativo.

### 1. Construir la imagen de Docker

Sitúate en la raíz del proyecto (donde se encuentra el archivo `Dockerfile`) y ejecuta el siguiente comando para compilar la imagen. Reemplaza `api-mediciones` por el nombre que prefieras:

docker build -t api-mediciones .

Adicionalmente es necesario construir la imagen del motor de LLM Ollama y descargar el modelo Llama3.1:8b

en la carpeta Llama3_1 ejecutar

docker build -t llm_mediciones .

### 2. Ejecutar el contenedor
Una vez construida la imagen, levanta el contenedor exponiendo el puerto 8000:

docker run -d -p 8000:8000 --name backend-mediciones api-mediciones

adicionalmente para el motor LLM ejecutar el contenedor exponiendo el puerto 11434 por defecto.

docker run -d -p 11434:11434 --name ollama llm_mediciones


🔌 Endpoints Principales
Una vez que la aplicación esté corriendo, FastAPI genera automáticamente la documentación interactiva. Se puede acceder a ella navegando a:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

Endpoint de Procesamiento
- POST    /api/v1/mediciones/procesar: Recibe y procesa los datos de los reportes para su posterior validación en el cliente.
- GET     /api/v1/usuarios  --Obtener Usuarios
- POST    /api/v1/usuarios  --Crear Usuario
- GET     /api/v1/usuarios/{user_id}  --Obtener Usuario
- PUT     /api/v1/usuarios/{user_id} --Actualizar Usuario
- DELETE  /api/v1/usuarios/{user_id} --Eliminar Usuario
- POST    /api/v1/procesar --Procesar Medicion
- GET     /api/v1/mediciones --Obtener Mediciones
- GET     /api/v1/mediciones/{medicion_id} --Obtener Medicion
- DELETE  /api/v1/mediciones/{medicion_id} --Eliminar una medición y sus variables asociadas
- PUT     /api/v1/mediciones/{medicion_id} --Modificar Medicion
- PUT     /api/v1/mediciones/{medicion_id}/validar --Validar Medicion
- PUT     /api/v1/mediciones/{medicion_id}/aprobar --Aprobar Medicion
- GET     /api/v1/mediciones/{medicion_id}/variables --Lista Variables X Medicion Id
- PUT     /api/v1/mediciones/{medicion_id}/variables --Reemplazar todas las variables de una medición.
⚠️ Notas de Configuración (CORS)
El backend está configurado con middlewares de CORS para permitir peticiones desde aplicaciones cliente separadas (por ejemplo, en el TFG se utiliza un frontend en Angular corriendo en http://localhost:4200). Si necesitas habilitar nuevos dominios u orígenes para producción, asegúrate de actualizarlos en la configuración de CORSMiddleware en el archivo main.py.
