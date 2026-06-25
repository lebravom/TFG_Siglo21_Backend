from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from models.usuario import Usuario

class ServicioUsuario:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def listar_usuarios(self) -> list[Usuario]:
        statement = select(Usuario)
        resultado = await self._db.exec(statement)
        return list(resultado.all())
    
    async def obtener_usuario(self, user_id:int) -> Usuario | None:
        statement = select(Usuario).where(Usuario.id == user_id)
        resultado = await self._db.exec(statement)
        return resultado.first()
    
    async def crear_usuario(self, usuario_nuevo: Usuario) -> Usuario:
        nuevo_usuario = Usuario(
            username = usuario_nuevo.username,
            email= usuario_nuevo.email,
            password_hash = usuario_nuevo.password_hash
        )
        try: 
            self._db.add(nuevo_usuario)
            await self._db.commit()
            await self._db.refresh(nuevo_usuario)
            return nuevo_usuario
        except IntegrityError:
            await self._db.rollback()
            raise ValueError

    async def actualizar_usuario(self, user_id: int, nombre_nuevo: str) -> Usuario | None:
        usuario = await self.obtener_usuario(user_id)
        if not usuario:
            return None
        usuario.nombre = nombre_nuevo
        await self._db.commit()
        await self._db.refresh(usuario)
        return usuario
    
    async def borrar_usuario(self, user_id: int) -> bool:
        usuario =await self.obtener_usuario(user_id)
        if not usuario:
            return False
        await self._db.delete(usuario)
        await self._db.commit()
        return True
