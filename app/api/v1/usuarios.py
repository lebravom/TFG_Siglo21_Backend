from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.db.database import sessionLocal
from app.services.servicioUsuario import ServicioUsuario
from app.models.usuario import Usuario


router = APIRouter()

def get_user_service() -> ServicioUsuario:
    return ServicioUsuario(session = sessionLocal)


@router.get("/usuarios", response_model=List[Usuario])
def obtener_usuarios(service: ServicioUsuario = Depends(get_user_service)):
    return service.listar_usuarios()


@router.post("/usuarios", response_model=Usuario)
def crear_usuario(usuario_nuevo: Usuario, service: ServicioUsuario = Depends(get_user_service)):
    try:
        return service.crear_usuario(usuario_nuevo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/usuarios/{user_id}", response_model=Usuario)
def obtener_usuario(user_id: int, service: ServicioUsuario = Depends(get_user_service)):
    usuario = service.obtener_usuario(user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario