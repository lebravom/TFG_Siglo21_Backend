from typing import List

from fastapi import APIRouter, Depends, HTTPException

from db.database import AsyncSessionLocal
from services.servicioUsuario import ServicioUsuario
from models.usuario import Usuario


router = APIRouter()

def get_user_service() -> ServicioUsuario:
    return ServicioUsuario(session = AsyncSessionLocal()) # pyright: ignore[reportArgumentType]


@router.get("/usuarios", response_model=List[Usuario])
async def obtener_usuarios(usuario_svc: ServicioUsuario = Depends(get_user_service)):
    return await usuario_svc.listar_usuarios()


@router.post("/usuarios", response_model=Usuario)
async def crear_usuario(usuario_nuevo: Usuario, service: ServicioUsuario = Depends(get_user_service)):
    try:
        return await service.crear_usuario(usuario_nuevo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/usuarios/{user_id}", response_model=Usuario)
async def obtener_usuario(user_id: int, service: ServicioUsuario = Depends(get_user_service)):
    usuario = await service.obtener_usuario(user_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario