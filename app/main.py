from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

# Importamos los modelos de SQLAlchemy y los esquemas de Pydantic
from db.database import engine
from core.logging import setup_logging
from core.config import config, origins
from api.v1 import usuarios
from api.v1 import mediciones

SQLModel.metadata.create_all(engine)
setup_logging()
app = FastAPI(title=config.app_name)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# INICIALIZACIÓN DE RUTAS
# ===========================================
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(mediciones.router, prefix="/api/v1")

# ==========================================
# INICIALIZACIÓN DE CORS
# ===========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

