import os
import tempfile
from io import BytesIO
from pypdf import PdfWriter, PdfReader
from docling.document_converter import DocumentConverter
from fastapi import UploadFile


# ==========================================
# Parametros globales de docling
#===========================================
os.environ["HF_HUB_OFFLINE"] = "1"


class servicioConversion:
    def __init__(self):
        self.converter = DocumentConverter()

    async def convertir_a_markdown(self, archivo: BytesIO) -> str:
        """
        Convierto un documento contenido en BytesIO a markdown utilizando Docling
        """
        
        archivo.seek(0)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(archivo.getvalue())
            tmp_path = tmp.name

        try:
            resultado = self.converter.convert(tmp_path)
            return resultado.document.export_to_markdown()
        except Exception as e:
            raise ValueError(f"Error en Docling: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)  

    
    async def extraer_pagina(self, file: UploadFile, pagina: int) -> BytesIO:
        """
        Extrae la página especificada de un PDF recibido como UploadFile.
        Los números de página comienzan en 1.
        Retorna un objeto BytesIO con el PDF de una sola página.
        Argumento: 
            file: Objeto UploadFile
        retorno:
            bytes: Contenido del nuevo PDF solo con la primer página.
        Raises:
            ValueError: Si el PDF está vacío o no tiene páginas.
        """
        contenido = await file.read()

        if not contenido:
            raise ValueError("El archivo está vacío")
        
        pdf_bytes= BytesIO(contenido)
        lector = PdfReader(pdf_bytes)

        if pagina < 1 or pagina > len(lector.pages):
            raise ValueError(f"La página {pagina} no existe. El PDF tiene {len(lector.pages)} páginas.")
        
        escritor = PdfWriter()

        escritor.add_page(lector.pages[pagina -1])

        output = BytesIO()
        escritor.write(output)
        output.seek(0)

        
        return output

    

    
        