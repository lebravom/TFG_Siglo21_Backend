from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    image_file: Mapped[str] = mapped_column(String(200), nullable=True, default=None)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    ultimo_acceso: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    @property
    def image_path(self) -> str | None:
        if self.image_file:
            return f"/static/profile_pics/{self.image_file}"
        return "static/profile_pics/default.jpg"

class tipo_analisis(Base):
    __tablename__ = "tipo_analisis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=True)
