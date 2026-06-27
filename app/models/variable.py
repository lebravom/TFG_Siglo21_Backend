from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Column, Relationship, Field, SQLModel, Text





if TYPE_CHECKING:
    from models.medicion import Medicion
    


class Variable(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    medicion_id: int = Field(foreign_key="medicion.id", ondelete="CASCADE")
    nuclideName: str = Field(
        max_length=50,
        description="El nombre del radionucleido identificado en la pagina 'NUCLIDE IDENTIFICATION REPORT'",
    )
    IdConfidence: float = Field(
        description="La confianza identificada para cada radionucleido en la pagina 'NUCLIDE IDENTIFICATION REPORT'",
    )
    Activity: str = Field(
        max_length=100,
        description="La actividad identificada en Bq/KG en la pagina 'NUCLIDE IDENTIFICATION REPORT'",
    )
    ActivityUncertainty: str = Field(
        max_length=100,
        description="La incerteza de la actividad en la pagina 'NUCLIDE IDENTIFICATION REPORT'",
    )
    # Relación inversa (Esta variable pertenece a una medición)
    medicion: Optional["Medicion"] = Relationship(back_populates="variables")

class ListaVariables(SQLModel, table=False):
    variables: List[Variable] = Field(description="Lista de radionucleidos variables identificados en la pagina 'NUCLIDE IDENTIFICATION REPORT' ")
    texto_markdown: Optional[str] = Field(
        default=None, 
        sa_column=Column(Text) # Le indicamos a SQLAlchemy que use TEXT en la DB
    )