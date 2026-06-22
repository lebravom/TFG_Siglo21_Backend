from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.usuario import Usuario

class ServicioUsuario:
    def __init__(self, session: Session):
        self._db = session

    def listar_usuarios(self) -> list[Usuario]:
        statement = select(Usuario)
        usuarios = self._db.exec(statement).all()
        return list(usuarios)
    
    def obtener_usuario(self, user_id:int) -> Usuario | None:
        statement = select(Usuario).where(Usuario.id == user_id)
        return self._db.exec(statement).first()
    
    def crear_usuario(self, usuario_nuevo: Usuario) -> Usuario:
        nuevo_usuario = Usuario(
            username = usuario_nuevo.username,
            email= usuario_nuevo.email,
            password_hash = usuario_nuevo.password_hash
        )
        try: 
            self._db.add(nuevo_usuario)
            self._db.commit()
            self._db.refresh(nuevo_usuario)
            return nuevo_usuario
        except IntegrityError:
            self._db.rollback()
            raise ValueError

    def actualizar_usuario(self, user_id: int, nombre_nuevo: str) -> Usuario | None:
        usuario = self.obtener_usuario(user_id)
        if not usuario:
            return None
        usuario.nombre = nombre_nuevo
        self._db.commit()
        self._db.refresh(usuario)
        return usuario
    
    def borrar_usuario(self, user_id: int) -> bool:
        usuario = self.obtener_usuario(user_id)
        if not usuario:
            return False
        self._db.delete(usuario)
        self._db.commit()
        return True
