from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario

@router.put("/usuarios/{user_id}", status_code=status.HTTP_202_ACCEPTED, response_model=Usuario)
async def actualizar_usuario(user_id: int, usuario_actualizado: Usuario, service: ServicioUsuario = Depends(get_user_service)):
    """
    Actualiza completamente un usuario.
    Todos los campos deben ser enviados en el cuerpo de la solicitud.
    """   
    try:
        usuario_res: Optional[Usuario] = await service.actualizar_usuario(user_id, usuario_actualizado)
        if usuario_res is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return usuario_res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
@router.delete("/usuarios/{user_id}",status_code=status.HTTP_200_OK)
async def eliminar_usuario(user_id: int, service: ServicioUsuario = Depends(get_user_service)):
    """
    Elimina el usuario especificado en el id, en caso que no lo encuentre retorna HTTP_404_NOT_FOUND
    """
    eliminado = await service.borrar_usuario(user_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o ya eliminado"
        )
    