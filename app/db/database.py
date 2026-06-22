from sqlmodel import Session, create_engine

DATABASE_URL = "sqlite:///./mediciones.db"

# 1. create_engine se importa desde sqlmodel (es un wrapper de SQLAlchemy)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

sessionLocal = Session(engine)


# 3. get_db se simplifica usando el manejador de contexto nativo Session de SQLModel
def get_db():
    with Session(engine) as session:
        yield session