from typing import Optional, List
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Column, Relationship, SQLModel, Field, Text

from app.models.variable import Variable




    


class Medicion(SQLModel, table=True):
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
    sampleType: str = Field(
        max_length=50,
        description="El estado o tipo de la muestra. Ej: 'SOLIDO'."
    )
    sampleGeometry: str = Field(
        max_length=50,
        description="La geometría o tamaño de la muestra. Ej: '250CM3'."
    )
    sampleTakenOn: str = Field(
        max_length=100,
        description="Fecha y hora de la toma de muestra. Ej: '02/01/2026 02:15:00 PM'."
    )
    acquisitionStarted: str = Field(
        max_length=100,
        description="Fecha y hora del inicio de adquisición. Ej: '12/01/2026 09:11:27 AM'."
    )
    texto_markdown: Optional[str] = Field(
        default=None, 
        sa_column=Column(Text) # Le indicamos a SQLAlchemy que use TEXT en la DB
    )
    variables: Mapped[List["Variable"]] = Relationship(sa_relationship=relationship(back_populates="medicion"))
    