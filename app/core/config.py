from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

# Origenes para configurar el CORS
origins = [
    "http://localhost:4200",     # Tu frontend Angular
    "http://127.0.0.1:4200",     # Variante por IP local
    "http://localhost:8000",     # El propio backend 
]

# ==========================================
# CONFIGURACIÓN DE OLLAMA
# ==========================================
ollama_config = {
    "OLLAMA_URL" : "http://localhost:11434/api/generate",
    "OLLAMA_MODEL" : "llama3.1:8b"
}
     



class Config(BaseSettings):
    app_name: str = "Mediciones"
    debug: bool = True
    db_user: str = "lbravo"
    db_password: str = "admin"
    db_name: str = "mediciones.db"

    @property
    def db_url(self):
        return f"sqlite:///./{self.db_name}"
    

config = Config()