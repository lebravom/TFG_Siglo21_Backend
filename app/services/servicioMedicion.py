from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select, func
from models.medicion import Medicion
from models.variable import ListaVariables, Variable
from sqlmodel.ext.asyncio.session import AsyncSession
from core.logging import logger



class servicioMedicion:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def listar_mediciones(self) -> list[Medicion]:
        statement = select(Medicion)
        resultado = await self._db.exec(statement)
        mediciones: list[Medicion] = list(resultado.all())
        return mediciones
    
    async def eliminar_medicion(self,medicion_id:int) -> bool:
        medicion = await self.obtener_medicion(medicion_id)

        if not medicion:
            return False
        await self._db.delete(medicion)
        await self._db.commit()
        return True
    

    async def obtener_medicion(self, medicion_id: int) -> Medicion | None:
        statement = select(Medicion).where(Medicion.id == medicion_id)
        resultado = await self._db.exec(statement)
        return resultado.one_or_none()
    
    async def actualizar_medicion(self, medicion_id: int, medicion_nueva: Medicion) -> Medicion | None:
        med = await self.obtener_medicion(medicion_id)
        if not med:
            return None
        
        med.sampleTitle = medicion_nueva.sampleTitle
        med.sampleDescription = medicion_nueva.sampleDescription
        med.sampleSize = medicion_nueva.sampleSize
        med.sampleType = medicion_nueva.sampleType
        med.sampleGeometry = medicion_nueva.sampleGeometry
        med.sampleTakenOn = medicion_nueva.sampleTakenOn
        med.acquisitionStarted = medicion_nueva.acquisitionStarted

        self._db.add(med)
        await self._db.commit()
        await self._db.refresh(med)
        return med

    async def obtener_ultimo_id(self) -> int:
        statement = select(func.max(Medicion.id))
        resultado = await self._db.exec(statement)
        ultimo = resultado.one()
        return ultimo if ultimo is not None else 0
    
    async def grabar_medicion(self, med: Medicion, list_var: ListaVariables) -> Medicion:
        """
        Guarda o actualiza una medición en la base de datos.
        También guarda las variables relacionadas.
        """
        try:
            # Agrego la medición y obtengo el ID generado por la base de datos
            async with self._db.begin():
                # Agregar la medición
                self._db.add(med)
                # Forzar la asignación del ID (sin commit)
                await self._db.flush() 
                if med.id is None:
                    raise ValueError("No se pudo generar el ID de la medición")
                await self._db.refresh(med)

                # Agregar cada variable con el ID de la medición
                for var in list_var.variables:
                    var.medicion_id = med.id
                    self._db.add(var)
                # Al salir del bloque, se hace commit automáticamente

            
            await self._db.refresh(med) 
  

            return med
        except Exception as e:
            await self._db.rollback()
            raise ValueError(f"Error al guardar la medición: {str(e)}")

    async def obtener_variables_de_medicion(self, medicion_id: int) -> list[Variable]:
        statement = select(Variable).where(Variable.medicion_id == medicion_id)
        variables = await self._db.exec(statement)
        variables = variables.all()
        return list(variables)
    
    async def actualizar_variables(self, medicion_id: int, variables_nuevas: list[Variable])-> list[Variable]:
        
        try: 
            # Iniciamos la transacción
            async with self._db.begin():
                # 1 Buscamos en la base las variables correspondientes a la medicion_id
                statement = select(Variable).where(Variable.medicion_id == medicion_id)
                resultados = await self._db.exec(statement)
                variables_viejas = resultados.all()
                
                # 2 Agregamos las variables nuevas a la base de datos. Comenzamos la Tx.
                    
                variables_creadas: list[Variable] = []
                for var_in in variables_nuevas:
                    nueva_var = Variable(
                        medicion_id=var_in.medicion_id, # Forzamos el ID de la medición actual
                        nuclideName=var_in.nuclideName,
                        IdConfidence=var_in.IdConfidence,
                        Activity=var_in.Activity,
                        ActivityUncertainty=var_in.ActivityUncertainty
                    )
                    self._db.add(nueva_var)
                    variables_creadas.append(nueva_var)

                # 3. Eliminar las variables viejas
                for var in variables_viejas:
                    await self._db.delete(var)
                
                
            for var in variables_creadas:
                await self._db.refresh(var)
                
            # 4 Retorno la lista de variables nuevas creadas.    
            return variables_creadas
        
        except SQLAlchemyError as e:
            logger.error(f"Error al actualizar variables para medición: {medicion_id}, error: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Error inesperado al actualizar variables: {str(e)}")
            raise


    async def validar_medicion(self, medicion_id: int)-> Medicion:
        """
        Valida una medicion en la base de datos estableciendo el campo Validada_en con el valor de la fecha actual del sistema.
        """
        try:
            statement = select(Medicion).where(Medicion.id == medicion_id)
            result = await self._db.exec(statement)
            medicion = result.one_or_none()
            
            if medicion is None:
                raise ValueError(f"Medición {medicion_id} no encontrada.")
            medicion.fecha_validacion = datetime.now(timezone.utc)
            await self._db.commit()
            await self._db.refresh(medicion)
            return medicion

        except ValueError:
            raise   # dejar que el endpoint lo convierta en 404
        except SQLAlchemyError as e:
            await self._db.rollback()         
            logger.error("Error al validar medición %s: %s", medicion_id, e)
            raise
        except Exception as e:
            await self._db.rollback()
            logger.exception("Error inesperado al validar medición %s: %s", medicion_id, e)
            raise
        
    async def aprobar_medicion(self, medicion_id: int)-> Medicion:
        """
        Aprueba una medicion en la base de datos estableciendo el campo aprobada_en con el valor de la fecha actual del sistema.
        """
        try:
            statement = select(Medicion).where(Medicion.id == medicion_id)
            result = await self._db.exec(statement)
            medicion = result.one_or_none()
            
            if medicion is None:
                raise ValueError(f"Medición {medicion_id} no encontrada.")
            medicion.fecha_aprobacion = datetime.now(timezone.utc)
            await self._db.commit()
            await self._db.refresh(medicion)
            return medicion

        except ValueError:
            raise   # dejar que el endpoint lo convierta en 404
        except SQLAlchemyError as e:
            await self._db.rollback()         
            logger.error("Error al aprobar medición %s: %s", medicion_id, e)
            raise
        except Exception as e:
            await self._db.rollback()
            logger.exception("Error inesperado al aprobar medición %s: %s", medicion_id, e)
            raise



