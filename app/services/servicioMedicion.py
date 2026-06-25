from sqlmodel import select, func
from models.medicion import Medicion
from models.variable import ListaVariables
from sqlmodel.ext.asyncio.session import AsyncSession




class servicioMedicion:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def listar_medicion(self) -> list[Medicion]:
        statement = select(Medicion)
        resultado = await self._db.exec(statement)
        mediciones: list[Medicion] = list(resultado.all())
        return mediciones
    
    async def obtener_medicion(self, medicion_id: int) -> Medicion | None:
        statement = select(Medicion).where(Medicion.id == medicion_id)
        resultado = await self._db.exec(statement)
        return resultado.one_or_none()
    
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