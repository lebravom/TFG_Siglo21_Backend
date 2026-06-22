from sqlmodel import Session, select

from models.medicion import medicion





class servicioMedicion:
    def __init__(self, session: Session):
        self._db = session

    def listar_medicion(self) -> list[medicion]:
        statement = select(medicion)
        mediciones = self._db.exec(statement).all()
        return list(mediciones)
    
    def obtener_medicion(self, medicion_id: int) -> medicion | None:
        statement = select(medicion).where(medicion.id == medicion_id)
        return self._db.exec(statement).first()
    
    #def guardar_medicion(self, medicion_nueva:medicion)-> medicion:
