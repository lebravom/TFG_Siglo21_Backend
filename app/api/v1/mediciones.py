from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from pydantic import ValidationError
from typing import Any, Dict
from sqlmodel import Session
from ollama import AsyncClient, ResponseError, chat
from services.servicioMedicion import servicioMedicion
from services.servicioConversion import servicioConversion
from models.medicion import medicion
from db.database import get_db
from app.core.config import ollama_config
from app.core.logging import logger


router = APIRouter()

MAX_FILE_SIZE_MB = 25 

def get_conversion_service() -> servicioConversion:
    return servicioConversion()

def get_medicion_service(db: Session = Depends(get_db)) -> servicioMedicion:
    return servicioMedicion(session = db)

@router.post("/procesar", status_code=status.HTTP_201_CREATED)
async def procesar_medicion(
    archivo: UploadFile = File(...),
    conversion_svc: servicioConversion = Depends(get_conversion_service),
    medicion_svc: servicioMedicion = Depends(get_medicion_service)
    ) -> Dict[str, Any]:

    """
    Recibe un archivo PDF con mediciones, lo convierte a Markdown,
    extrae los datos de la medicion y los guarda en la base de datos.
    Devuelve el ID de la medición creada
    """

    # Validaciones de formato
    if not archivo.filename or not archivo.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "El archivo debe ser un documento tipo PDF"
            )
    # Validación de tamaño
    content = await archivo.read()
    file_size_mb = len(content) /(1024*1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_MB} MB."
        )
    logger.info("El archivo es del tamaño correcto.")
    # Reiniciar el puntero del archivo
    await archivo.seek(0)

    # Dado que es un PDF y que pesa menos de 25 MB se procede a convertir a Markdown
    logger.info("El archivo esta convirtiendose.")
    try:
        markdown_result = await conversion_svc.convertir_a_markdown(archivo)
      

    except ValueError as e:
        logger.error("Error en conversión de PDF: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo procesar el archivo PDF: {e}"
        )
    except Exception as e:
        logger.exception("Error inesperado en conversión")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al convertir el archivo"
        )
    # 4. Grabado de la nueva medición en la tabla de auditoria


    # 4. Extracción de los datos de la medición (Envio al servicio de OLLAMA)
    try:
        datos_medicion = await extraer_datos_desde_markdown(markdown_result)
    except ValueError as e:
        logger.error("Error extrayendo datos de medición: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato de medición no reconocido: {e}"
        )
    except RuntimeError as e:
        # Fallos de comunicación o inesperados
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    
    # Almacenar datos de medición en la base de datos.
    #try: 
    #    medicion_id = medicion_svc.guardar_medicion(datos_medicion.model_dump())
    #except Exception as e:
    #    logger.exception("Error al guardar la medición en la base de datos")
    #    raise HTTPException(
    #        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #        detail="Error interno al guardar la medición"
    #    )
    #
    return {
        "filename": archivo.filename,
        "status": "success",
        "medicion_id": "",
        "medicion": datos_medicion.model_dump(),  # opcional: devuelve también los datos extraídos
        "detail": "Medición procesada y almacenada correctamente"
    }



async def extraer_datos_desde_markdown(markdown: str) -> medicion:
    """ 
    Envio el markdown convertido a ollama esperando un objeto medición a la vuelta.
    """

    esquema_medicion = medicion.model_json_schema()

    try:
        client = AsyncClient()
        response = await client.chat(
            model=ollama_config["OLLAMA_MODEL"],
            messages=[{
                "role": "user",
                "content": (
                    "Extrae la información de la medición contenida en el siguiente texto Markdown. "
                    "Devuelve **exclusivamente** un objeto JSON que cumpla con el esquema proporcionado.\n\n"
                    f"Esquema: {esquema_medicion}\n\n"
                    f"Texto Markdown:\n{markdown}"
                )}],
            format=esquema_medicion,
            options={"temperature": 0}
        )

        raw_json = response["message"]["content"]
        medicion_resultado = medicion.model_validate_json(raw_json)
        logger.info("Extracción exitosa :%s", medicion_resultado)
        return medicion_resultado

    except ResponseError as e:
        logger.error("Error en la respuesta de Ollama: %s", e)
        raise ValueError(f"Ollama no pudo procesar la solicitud: {e}")
    except ValidationError as e:
        logger.error("JSON recibido no cumple con el modelo Medicion: %s", e)
        raise ValueError(f"El formato de los datos extraídos no es válido: {e}")
    except Exception as e:
        logger.exception("Error inesperado al llamar a Ollama")
        raise RuntimeError("Fallo en la comunicación con el servicio Ollama")