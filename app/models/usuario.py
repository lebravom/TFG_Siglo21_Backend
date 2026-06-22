from datetime import datetime, UTC
from typing import Optional
from sqlmodel import SQLModel, Field, DateTime, Column
from pydantic import EmailStr

class Usuario(SQLModel, table=True):

    # El ID es opcional en el código para permitir instanciar el objeto antes de guardarlo en la DB
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    
    # nullable=False es implícito al usar 'str' en lugar de 'Optional[str]'
    username: str = Field(max_length=50, unique=True)
    
    # Implementamos EmailStr para ganar la validación automática de Pydantic
    email: EmailStr = Field(max_length=100, unique=True)
    
    # Optional[str] hace que nullable=True sea implícito en la base de datos
    image_file: Optional[str] = Field(default=None, max_length=200)
    
    password_hash: str = Field(max_length=128)
    
    # nullable=False es implícito por el tipo 'bool'
    activo: bool = Field(default=True)
    
    # Usamos default_factory para ejecutar lambda: datetime.now(UTC) a nivel aplicación
    # y sa_column para asegurar el uso de DateTime(timezone=True) en SQLAlchemy
    ultimo_acceso: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    creado_en: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Las propiedades y métodos de clase regulares de Python funcionan exactamente igual
    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/static/profile_pics/{self.image_file}"
        return "static/profile_pics/default.jpg"