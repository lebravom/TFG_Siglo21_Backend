# Usamos la imagen oficial de Ollama como base
FROM ollama/ollama:latest

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY run-ollama.sh /run-ollama.sh

# Corregir finales de línea de Windows a Linux y dar permisos
RUN sed -i 's/\r$//' /run-ollama.sh && chmod +x /run-ollama.sh || exit 0

# Ejecutar el script
RUN /run-ollama.sh

# Comando por defecto para iniciar el servidor al arrancar el contenedor
RUN ollama serve & \
    sleep 5 && \
    ollama pull llama3.1:8b

EXPOSE 11434