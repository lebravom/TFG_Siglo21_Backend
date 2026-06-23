from typing import Optional, TYPE_CHECKING
from sqlmodel import ForeignKey, Relationship, SQLModel, Field

if TYPE_CHECKING:
    from models.medicion import Medicion

class Variable(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    medicion_id: int = Field(foreign_key="medicion.id")
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
