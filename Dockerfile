# syntax=docker/dockerfile:1
FROM quay.io/pypa/manylinux_2_28_x86_64

# Ajuste de entorno recomendado para contenedores
ENV UV_COMPILE_BYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV UV_SKIP_WHEEL_FILENAME_CHECK=1

WORKDIR /app

# Copiar primero los archivos de dependencias para aprovechar la caché de capas de Docker
COPY pyproject.toml uv.lock ./

# Instalar dependencias
RUN uv sync --locked

# Copiar el resto del código fuente
COPY . .

# Exponer el puerto
EXPOSE 8000

# Ejecutar la aplicación
# Nota: Cambia 'main.py' por el nombre de tu archivo de entrada si es distinto
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]