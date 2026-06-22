import os
import tempfile
from docling.document_converter import DocumentConverter
from fastapi import Path, UploadFile


# ==========================================
# Parametros globales de docling
#===========================================
os.environ["HF_HUB_OFFLINE"] = "1"


class servicioConversion:
    def __init__(self):
        self.converter = DocumentConverter()

    async def convertir_a_markdown(self, archivo: UploadFile) -> str:
        # Extraigo la extensión original del archivo (ej. '.pdf')
        extension = Path(archivo.filename).suffix if archivo.filename else ".pdf"

        # Creo un archivo físico temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            content = await archivo.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Convertir el documento
            resultado = self.converter.convert(tmp_path)

            # 3 exportar el resultado a markdown
            texto_markdown = resultado.document.export_to_markdown()

            return texto_markdown
        
        except Exception as e:
            # Agrego logs más específicos si falla el OCR o la conversión
            raise ValueError(f"Error al procesar el documento con Docling: {str(e)}")
            
        finally:
            # 4. Limpieza garantizada: Eliminar el archivo temporal del disco
            # Se ejecuta siempre, incluso si Docling lanza una excepción
            if os.path.exists(tmp_path):
                os.remove(tmp_path)     
        