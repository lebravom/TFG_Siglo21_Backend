#!/bin/bash

# Iniciar el servidor en segundo plano
ollama serve &
PID=$!
# Esperar a que el servidor responda (Check de salud)
echo "Esperando a que el servidor de Ollama arranque..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 2
done

echo "Servidor listo. Descargando modelo qwen3-vl:4b..."
ollama pull qwen3-vl:4b
echo "Modelo descargado. Deteniendo el servidor..."
kill $PID
WAIT $PID 2>/dev/null
echo "Servidor detenido. Listo para iniciar con el modelo descargado."
exit 0