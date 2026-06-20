from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    id: UUID
    nombre: str
    apellido: str
    email: EmailStr
    password_hash: str
    rol: str = Field(default="user")
    activo: bool = Field(default=True)
    ultimo_acceso: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    creado_en: datetime
    image_file: Optional[str] = None


class ResultadoMedicion(BaseModel):
    sampleTitle: str = Field(description="El nombre o título de la muestra. En el documento suele aparecer como 'Sample Title'.")
    sampleDescription: str = Field(description="La descripción o identificación de la muestra. En el documento puede aparecer bajo 'Sample Description' o 'Sample Identification'.")
    sampleSize: str = Field(description="El tamaño, peso o volumen de la muestra, incluyendo su unidad de medida (ej. KG o CM3). Aparece como 'Sample Size'.")


class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True) 
    image_path: str 