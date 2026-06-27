# API de Procesamiento de Mediciones

Backend desarrollado con **FastAPI** para la gestión, procesamiento y extracción de datos de mediciones y reportes técnicos de laboratorio.

Este servicio expone endpoints para integrar los resultados de mediciones en el sistema principal, permitiendo validar, aprobar, estructurar y consultar los datos extraídos.

## 🚀 Tecnologías Principales

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Gestión de dependencias:** [uv](https://github.com/astral-sh/uv) 
* **Contenedores:** Docker & Docker Compose
* **Lenguaje:** Python 3.12+

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

```bash
docker build -t api-mediciones .
