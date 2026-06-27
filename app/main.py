from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

# Importamos los modelos de SQLAlchemy y los esquemas de Pydantic
from db.database import engine
from core.logging import setup_logging
from core.config import config
from api.v1 import usuarios
from api.v1 import mediciones


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización asíncrona: crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Cierre (opcional): si tienes conexiones que cerrar
    await engine.dispose()

app = FastAPI(
    title=config.app_name,
    lifespan=lifespan  # <-- asigna aquí el manejador de ciclo de vida
)



setup_logging()
app = FastAPI(title=config.app_name)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Origenes para configurar el CORS
origins = [
    "http://localhost:4200",     # Tu frontend Angular
    "http://127.0.0.1:4200",     # Variante por IP local
    "http://localhost:8000",     # El propio backend 
]

# ==========================================
# INICIALIZACIÓN DE CORS
# ===========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ==========================================
# INICIALIZACIÓN DE RUTAS
# ===========================================
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(mediciones.router, prefix="/api/v1")

