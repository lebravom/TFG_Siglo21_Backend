from dotenv import load_dotenv
from pydantic import SecretStr # type: ignore 
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()



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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def db_url(self):
        return f"sqlite:///./{self.db_name}"
    
    secret_key: str = "SecretKey"
    algorithm:str ="H256"
    access_token_expire_minutes: int = 60

config = Config() # type: ignore[call-arg] # Loaded from .env file