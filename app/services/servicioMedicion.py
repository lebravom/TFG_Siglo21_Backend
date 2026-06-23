from sqlmodel import Session, select, func

from models.medicion import Medicion





class servicioMedicion:
    def __init__(self, session: Session):
        self._db = session

    def listar_medicion(self) -> list[Medicion]:
        statement = select(Medicion)
        mediciones = self._db.exec(statement).all()
        return list(mediciones)
    
    def obtener_medicion(self, medicion_id: int) -> Medicion | None:
        statement = select(Medicion).where(Medicion.id == medicion_id)
        return self._db.exec(statement).first()
    
    def obtener_ultimo_id(self) -> int | None:
        statement = select(func.max(Medicion.id))
        return self._db.exec(statement).one()
    
    #def guardar_medicion(self, medicion_nueva:medicion)-> medicion:
