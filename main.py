import logging
import json
import asyncio
import tempfile
import os

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ollama import chat
from pathlib import Path
from docling.document_converter import DocumentConverter


# Importamos los modelos de SQLAlchemy y los esquemas de Pydantic
from schemas import ResultadoMedicion
from database import Base, engine

Base.metadata.create_all(bind=engine)




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
# INICIALIZAMOS DOCLING
#===========================================
os.environ["HF_HUB_OFFLINE"] = "1"
converter = DocumentConverter()

# ==========================================
# CONFIGURACIÓN DE OLLAMA
# ==========================================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b" 




app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _extract_text_from_pdf(file_path: Path) -> str:
    logger.info(f"Extrayendo texto del archivo {file_path} con pdfplumber...")
    
    result = converter.convert(str(file_path))

    document = getattr(result, "document", None)
                       
    if document is not None and hasattr(document, "export_to_markdown"):
        texto_markdown = document.export_to_markdown()
    elif hasattr(result, "export_to_markdown"):
        texto_markdown = result.document.export_to_markdown()
    else:
        logger.error("El documento no contiene texto extraíble o es enteramente un PDF escaneado (imagen).")
        raise ValueError("No se encontró texto extraíble en el PDF.")

    logger.info("Conversión a markdown exitosa")
    return str(texto_markdown)

async def _query_ollama(text: str):
    logger.info(f"Enviando petición a Ollama en {OLLAMA_URL} con JSON Schema...")
    
    
    prompt = [{
        'role' : 'user',
        'content' : f"""Eres un asistente experto en extracción de datos de reportes de laboratorio (Gamma Spectrum Analysis)., 
        Tu tarea es analizar el siguiente fragmento de texto extraído de un PDF y extraer exactamente tres valores.          
                                                                                                                            
        Instrucciones de extracción:        
        - Busca 'Sample Title' y asígnalo al campo sample_name.
        - Busca 'Sample Description' o 'Sample Identification' y combina su contenido si es necesario. Asígnalo al campo sample_description.
        - Busca 'Sample Size' (asegúrate de incluir el número y la unidad, por ejemplo 'KG') y asígnalo al campo sample_size.

        Devuelve EXCLUSIVAMENTE un objeto JSON válido que cumpla con el esquema proporcionado. No agregues texto introductorio ni explicaciones.

        Texto del reporte:
        ------------------
        {text}
        ------------------""",
    }]
    
    
    
    
    response = chat (
        model=OLLAMA_MODEL,
        messages=prompt,
        format=ResultadoMedicion.model_json_schema(),
        options={'temperature': 0},
    )

    response_content = response.message.content
    if response_content is None:
        logger.error("Ollama retornó contenido vacío.")
        raise RuntimeError("Ollama returned no content.")

    resultados = ResultadoMedicion.model_validate_json(response_content)

    print(resultados)
    # payload : dict[str, Any]= {
    #     "model": OLLAMA_MODEL,
    #     "prompt": prompt,
    #     "format": ResultadoMedicion.model_json_schema(),  # Obligamos a Ollama a usar este esquema JSON
    #     "stream": False
    # }

    # resultado: list[dict[str, Any]] = []  
    # try:
    #     async with httpx.AsyncClient(timeout=600.0) as client:
    #         response = await client.post(OLLAMA_URL, json=response)
    #         response.raise_for_status()
    #         data = response.json()
 
            # La respuesta vendrá como un string en formato JSON gracias al parámetro "format"
        #    raw_response = data.get("response", "{}")
            
            
            # Convertimos el string JSON devuelto por la IA a un diccionario de Python
        #     resultado_estructurado = ResultadoMedicion.model_validate_json(raw_response)
        #     resultado.append({
        #         "sampleTitle": resultado_estructurado.sampleTitle,
        #         "sampleDescription": resultado_estructurado.sampleDescription,
        #         "sampleSize": resultado_estructurado.sampleSize
        #     })


    return resultados
            
    # except resultados.JSONDecodeError:
    #     logger.error("Ollama devolvió una respuesta que no es un JSON válido.")
    #     raise RuntimeError("Fallo de formato: La IA no respetó el esquema JSON.")
    



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
            logger.info(f"Texto extraído:\n{text_result}...")

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