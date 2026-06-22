from typing import Optional, List
from sqlmodel import Relationship, SQLModel, Field
from models.variable import Variables

class Mediciones(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    sampleTitle: str = Field(
        max_length=255,
        description="El nombre o título de la muestra. En el documento suele aparecer como 'Sample Title'."
    )
    sampleDescription: str = Field(
        description="La descripción o identificación de la muestra. En el documento puede aparecer bajo 'Sample Description' o 'Sample Identification'."
    )
    sampleSize: str = Field(
        max_length=100,
        description="El tanaño, peso o volumen de la muestra, incluyendo su unidad de medida."
    )

    variables: List["Variables"] = Relationship(back_populates="medicion")
