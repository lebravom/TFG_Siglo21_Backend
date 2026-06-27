import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError
from typing import List, Optional, TypeVar
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel
from ollama import AsyncClient, ResponseError, chat     # pyright: ignore[reportUnknownVariableType, reportUnusedImport]  # noqa: F401
from services.servicioMedicion import servicioMedicion
from services.servicioConversion import servicioConversion
from models.medicion import Medicion 
from models.variable import Variable
from models.variable import ListaVariables
from db.database import get_db
from core.config import ollama_config
from core.logging import logger
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter()

MAX_FILE_SIZE_MB = 25 

T = TypeVar("T", bound=SQLModel)

def get_conversion_service() -> servicioConversion:
    return servicioConversion()

def get_medicion_service(db: AsyncSession = Depends(get_db)) -> servicioMedicion:
    return servicioMedicion(session = db)

def _validar_archivo(archivo: UploadFile, contenido: bytes) -> None:
    """Valida formato y tamaño del archivo. Lanza HTTPException si falla."""
    if not archivo.filename or not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un documento tipo PDF.",
        )
    size_mb = len(contenido) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_MB} MB.",
        )
    
async def _extraer_paginas_markdown(
    archivo: UploadFile,
    conversion_svc: servicioConversion,
) -> tuple[str, str]:
    """Extrae y convierte a Markdown las páginas 1 y 2 del PDF."""
    try:
        await archivo.seek(0)
        pagina_1 = await conversion_svc.extraer_pagina(archivo, 1)
        await archivo.seek(0)
        pagina_2 = await conversion_svc.extraer_pagina(archivo, 2)

        markdown_cabecera = await conversion_svc.convertir_a_markdown(pagina_1)
        markdown_variables = await conversion_svc.convertir_a_markdown(pagina_2)

        logger.debug("Markdown cabecera: %s", markdown_cabecera)
        logger.debug("Markdown variables: %s", markdown_variables)

        return markdown_cabecera, markdown_variables

    except ValueError as e:
        logger.error("Error en conversión de PDF: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo procesar el archivo PDF: {e}",
        )
    except Exception as e:
        logger.exception("Error inesperado en conversión")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al convertir el archivo.",
        ) from e


async def _extraer_modelos(markdown_cabecera: str,markdown_variables: str) -> tuple[Medicion, ListaVariables]:
    """
    Extrae los modelos Pydantic desde el Markdown via Ollama.
    Retorna una tupla (Medicion, ListaVariables) con tipos concretos.
    """
    try:
        tarea_cabecera = _extraer_datos_desde_markdown(markdown_cabecera, Medicion)
        tarea_variables = _extraer_datos_desde_markdown(markdown_variables, ListaVariables)

        medicion, lista_variables = await asyncio.gather(tarea_cabecera, tarea_variables)
        logger.info("Datos de cabecera extraídos: %s", medicion)
        logger.info("Datos de variables extraídos: %s", lista_variables)

        return medicion, lista_variables
    
    except ValueError as e:
        logger.error("Error extrayendo datos de medición: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato de medición no reconocido: {e}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e



async def _extraer_datos_desde_markdown(markdown: str, esquema:type[T]) -> T:
    """ 
    Envía el markdown a Ollama y retorna una instancia del esquema recibido.
    El TypeVar T preserva el tipo concreto (Medicion, ListaVariables, etc.)
    """

    esquema_medicion = esquema.model_json_schema()

    logger.info(f"Enviando petición a Ollama en {ollama_config['OLLAMA_URL']} con JSON Schema...")
    
    try:
        client = AsyncClient()
        response = await client.chat( # pyright: ignore[reportUnknownMemberType]
            model=ollama_config["OLLAMA_MODEL"],
            messages=[{
                "role": "user",
                "content": (
                    "Extrae la información de la medición contenida en el siguiente texto Markdown. "
                    "Devuelve **exclusivamente** un objeto JSON que cumpla con el esquema proporcionado.\n\n"
                    f"Esquema: {esquema_medicion}\n\n"
                    f"Texto Markdown:\n{markdown}"
                )}],
            format=esquema.model_json_schema(),
            options={"temperature": 0}
        )
        logger.info("Chat exitoso, respuesta %s", response)
    
        raw_json = response["message"]["content"]
        medicion_resultado = esquema.model_validate_json(raw_json)
        logger.info("Extracción exitosa :%s", medicion_resultado)
        return medicion_resultado  
    
    except ResponseError as e:
        logger.error("Error en la respuesta de Ollama: %s", e)
        raise ValueError(f"Ollama no pudo procesar la solicitud: {e}")
    except ValidationError as e:
        logger.error("JSON recibido no cumple con el modelo Medicion: %s", e)
        raise ValueError(f"El formato de los datos extraídos no es válido: {e}")
    except Exception as e:  # noqa: F841
        logger.exception("Error inesperado al llamar a Ollama")
        raise RuntimeError("Fallo en la comunicación con el servicio Ollama")
    

@router.post("/procesar", status_code=status.HTTP_201_CREATED)
async def procesar_medicion(
    archivo: UploadFile = File(...),
    conversion_svc: servicioConversion = Depends(get_conversion_service),
    medicion_svc: servicioMedicion = Depends(get_medicion_service),
) -> Medicion:
    """
    Recibe un PDF con mediciones, lo convierte a Markdown,
    extrae los datos estructurados y los persiste en la base de datos.
    Devuelve la medición creada.
    """
    # 1. Validar archivo
    contenido = await archivo.read()
    _validar_archivo(archivo, contenido)
    logger.info("Archivo '%s' validado correctamente.", archivo.filename)

    # 2. Convertir páginas a Markdown
    logger.info("Convirtiendo archivo a Markdown...")
    markdown_cabecera, markdown_variables = await _extraer_paginas_markdown(
        archivo, conversion_svc
    )

    # 3. Extraer modelos desde Markdown via Ollama
    medicion, lista_variables = await _extraer_modelos(
        markdown_cabecera, markdown_variables
    )

    # 4. Enriquecer modelos con el texto fuente
    medicion.texto_markdown = markdown_cabecera
    lista_variables.texto_markdown = markdown_variables

    # 5. Persistir y retornar
    logger.info("Grabando medición en la base de datos...")
    return await medicion_svc.grabar_medicion(medicion, lista_variables)


@router.get("/mediciones", response_model=list[Medicion])
async def obtener_mediciones(medicion_svc: servicioMedicion = Depends(get_medicion_service)):
    return await medicion_svc.listar_mediciones()

@router.get("/mediciones/{medicion_id}", response_model=Medicion)
async def obtener_medicion(medicion_id: int, medicion_svc: servicioMedicion = Depends(get_medicion_service)):
    medicion = await medicion_svc.obtener_medicion(medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="Medicion no encontrado¿a")
    return medicion

@router.delete("/mediciones/{medicion_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una medición y sus variables asociadas")
async def eliminar_medicion(medicion_id: int, service: servicioMedicion = Depends(get_medicion_service)):
    """
    Elimina la medición identificada por 'medicion_id'
    Gracias a la casacada configurada en los modelos, también se eliminan
    automáticamente todas las variables vinculadas a esa medición.
    """
    logger.info(f"Eliminando medición con ID: {medicion_id}")
    try:
        await service.eliminar_medicion(medicion_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada"
        )
    except SQLAlchemyError as e:
        logger.error(f"Error de BD al eliminar medición {medicion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "Error al eliminar la medición (puede estar en uso o tener depedencia no cascadeable)."
        )
    except Exception as e:
        logger.exception(f"Error inesperado al eliminar medición {medicion_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor.",
        )

@router.put("/mediciones/{medicion_id}", response_model=Medicion, status_code=status.HTTP_202_ACCEPTED)
async def modificar_medicion(medicion_id: int, medicion_nueva: Medicion, service: servicioMedicion = Depends(get_medicion_service)):
     """
     Actualiza completamente una medición
     Todos los campos son enviados nuevamente en el cuerpo de la solicitud
     """

     try:
         medicion_modificada: Optional[Medicion] = await service.actualizar_medicion(medicion_id, medicion_nueva)
         if medicion_modificada is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Medición no encontrada")
         return medicion_modificada
     except ValueError as e:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/mediciones/{medicion_id}/validar", response_model=Medicion, status_code=status.HTTP_200_OK)
async def validar_medicion(medicion_id: int, service: servicioMedicion = Depends(get_medicion_service)):
    """
    Valida una medición en la base de datos.
    Establece el campo fecha_validacion en la fecha actual del sistema. 
    """
    logger.info(f"El parametro recibido es: {medicion_id}, del tipo {type(medicion_id)}")
    try:
         medicion_modificada: Optional[Medicion] = await service.validar_medicion(medicion_id)
         if medicion_modificada.id is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Medición no encontrada")
         return medicion_modificada
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))





@router.get("/mediciones/{medicion_id}/variables", response_model=list[Variable], status_code=status.HTTP_200_OK)
async def lista_variables_x_medicion_id(medicion_id: int, service: servicioMedicion = Depends(get_medicion_service)):
    """
    Devuelve una lista de variables correspondientes al ID de medición suministrado
    """
    try:
        resultado = await service.obtener_variables_de_medicion(medicion_id)
        if resultado.pop is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variables para la medición N°: {medicion_id}, no identificadas")
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= f"Ocurrio un error {e}")
    

@router.put("/mediciones/{medicion_id}/variables", response_model=list[Variable], status_code=status.HTTP_200_OK, summary="Reemplazar todas las variables de una medición.")
async def actualizar_variables(
    medicion_id: int,
    variables_in: List[Variable],
    servicio: servicioMedicion = Depends(get_medicion_service)
):
    """
    Actualizamos todas las variables asociadas a la medición.
    En caso que se agreguen mas variables, se insertan, similar a un upsert.
    """
    try:
        # Llamamos al servicio pasando el ID de la ruta y la lista del body
        variables_orm = [
            Variable(
                medicion_id = medicion_id,
                nuclideName=var.nuclideName,
                IdConfidence=var.IdConfidence,
                Activity=var.Activity,
                ActivityUncertainty=var.ActivityUncertainty
            )
            for var in variables_in
        ]
        
        # Llamar al serivicio 
        resultado_orm = await servicio.actualizar_variables(medicion_id, variables_orm)

        #convertir los objetos ORM a esquemas de respuestas.
        return resultado_orm

    except Exception as e:
        logger.exception(f"Error inesperado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor.",
        )