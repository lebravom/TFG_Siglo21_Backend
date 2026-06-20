from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Optional
from pathlib import Path
import pdfplumber
import httpx 

# Importamos los modelos de SQLAlchemy y los esquemas de Pydantic
from schemas import MedicionBE7
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

import logging
import json
import asyncio
import tempfile


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

origins = [
    "http://localhost:4200",     # Tu frontend Angular
    "http://127.0.0.1:4200",     # Variante por IP local
    "http://localhost:8000",     # El propio backend 
]


# ==========================================
# CONFIGURACIÓN DE OLLAMA
# ==========================================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b" 


# Generamos el esquema JSON a partir del modelo de Pydantic
ESQUEMA_JSON_BE7: dict[str, Any] = MedicionBE7.model_json_schema()


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _extract_text_from_pdf(file_path: Path) -> str:
    logger.info(f"Extrayendo texto del archivo {file_path} con pdfplumber...")
    texto_completo: list[str] = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for num, page in enumerate(pdf.pages):
                texto_pagina = page.extract_text()
                if texto_pagina:
                    texto_completo.append(texto_pagina)
                else:
                    logger.warning(f"No se pudo extraer texto de la página {num + 1}. Podría ser una imagen.")
        
        if not texto_completo:
            logger.error("El documento no contiene texto extraíble o es enteramente un PDF escaneado (imagen).")
            raise ValueError("No se encontró texto extraíble en el PDF.")
            
        logger.info("Extracción de texto exitosa.")
        # Unimos las páginas separándolas por un doble salto de línea
        return "\n\n".join(texto_completo)
        
    except Exception as e:
        logger.error(f"Fallo crítico procesando el PDF: {e}")
        raise RuntimeError(f"Fallo en la extracción con pdfplumber: {e}")


async def _query_ollama(text: str) -> dict[str,Any]:
    """Envía el texto a Ollama exigiendo una salida estructurada para BE-7."""
    logger.info(f"Enviando petición a Ollama en {OLLAMA_URL} con JSON Schema...")
    
    prompt = (
        "Extract only the precise text content from the provided Markdown. Output only the plain text sequence."
        f"Document Text:\n{text}"
    )
    
    payload : dict[str, Any]= {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "format": ESQUEMA_JSON_BE7,  # Obligamos a Ollama a usar este esquema JSON
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            # La respuesta vendrá como un string en formato JSON gracias al parámetro "format"
            raw_response = data.get("response", "{}")
            
            # Convertimos el string JSON devuelto por la IA a un diccionario de Python
            resultado_estructurado = json.loads(raw_response)
            return resultado_estructurado
            
    except json.JSONDecodeError:
        logger.error("Ollama devolvió una respuesta que no es un JSON válido.")
        raise RuntimeError("Fallo de formato: La IA no respetó el esquema JSON.")
    except Exception as e:
        logger.error(f"Error consultando a Ollama: {e}")
        raise RuntimeError(f"Error en la inferencia de la IA: {e}")



@app.post("/api/v1/mediciones/procesar")
async def extract_text(file: UploadFile = File(...)):
    logger.info(f"Petición entrante en /mediciones/procesar. Archivo recibido: {file.filename}")

    # Leer el archivo a memoria primero para no perder el stream del upload file
    file_content = await file.read()
    suffix = Path(file.filename or "uploaded-file").suffix

    async def generador_eventos():
        temp_path = None
        try:
            # Evento 1: Recepción del archivo
            yield f"data: {json.dumps({'status': 'Archivo recibido', 'progress': 10})}\n\n"
            await asyncio.sleep(0.5) # pausa para asegurar el flush del buffer http

            # Validación: Asegurar que es un PDF
            if suffix.lower() != ".pdf":
                raise ValueError("El archivo procesado debe ser un documento PDF.")

            # Evento 2: Creación del archivo temporal
            logger.info("Creando archivo temporal para procesamiento...")
            yield f"data: {json.dumps({'status': 'Creando archivo temporal para procesamiento', 'progress': 20})}\n\n"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(file_content)
                logger.info(f"Archivo guardado exitosamente en disco: {temp_path}")

            # Evento 3: Procesamiento del archivo con pdfplumber
            logger.info("Iniciando la extracción de texto con pdfplumber...")
            yield f"data: {json.dumps({'status': 'En cola de extracción de texto...', 'progress': 30})}\n\n"

            extraction_task = asyncio.create_task(asyncio.to_thread(_extract_text_from_pdf, temp_path))

            # Emitir latido mientras la tarea no termine
            latido = 0
            while not extraction_task.done():
                yield f"data: {json.dumps({'status': f'Analizando documento ({latido}s)...', 'progress': 40})}\n\n"

                try:
                    # Usar asyncio.shield para que el timeout NO cancele la tarea
                    await asyncio.wait_for(asyncio.shield(extraction_task), timeout=3.0)
                except asyncio.TimeoutError:
                    latido += 3
                    continue
            
            text_result = extraction_task.result()

            # Imprimir un resumen del texto extraído en log nivel DEBUG para no saturar la consola
            logger.debug(f"Texto extraído:\n{text_result}...")

            ollama_task = asyncio.create_task(_query_ollama(text_result))
            
            latido_ollama = 0
            while not ollama_task.done():
                yield f"data: {json.dumps({'status': f'Estructurando datos ({latido_ollama}s)...', 'progress': 75})}\n\n"
                try:
                    await asyncio.wait_for(asyncio.shield(ollama_task), timeout=3.0)
                except asyncio.TimeoutError:
                    latido_ollama += 3
                    continue

            # final_ai_result ahora es un diccionario (JSON) y no un string de texto libre
            final_ai_result = ollama_task.result()

            logger.info(f"Datos estructurados extraídos: {final_ai_result}")
            yield f"data: {json.dumps({'status': 'Extracción de BE-7 completada', 'progress': 100, 'result': final_ai_result})}\n\n"
            await asyncio.sleep(1)

            logger.info("Extracción completada exitosamente.")
            yield f"data: {json.dumps({'status': 'Extracción de texto completada exitosamente', 'progress': 100, 'result': text_result})}\n\n"
            await asyncio.sleep(1) # Pausa para asegurar que uvicorn vacíe los buffer TCP.

        except Exception as e:
            logger.error(f"Error durante el procesamiento del archivo: {e}", exc_info=True)
            yield f"data: {json.dumps({'status': 'Error durante el procesamiento del archivo', 'progress': 100, 'error': str(e)})}\n\n"
            await asyncio.sleep(1) # Pausa para asegurar que uvicorn vacíe los buffer TCP.
        finally:
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                    logger.info(f"Archivo temporal eliminado: {temp_path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo temporal {temp_path}: {e}")
                    
    return StreamingResponse(generador_eventos(), media_type="text/event-stream")


@app.get("/")
def home():
    return {"message": "Hello from mediciones!"}