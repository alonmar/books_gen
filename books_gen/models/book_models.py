"""
Modelos de datos para la aplicación.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class BookStyle(str, Enum):
    """Estilos literarios disponibles para la generación de libros."""

    NARRATIVO = "narrativo"
    DESCRIPTIVO = "descriptivo"
    DIALOGADO = "dialogado"
    EXPOSITIVO = "expositivo"
    ARGUMENTATIVO = "argumentativo"
    POETICO = "poetico"
    CIENCIA_FICCION = "ciencia_ficcion"
    FANTASIA = "fantasia"
    TERROR = "terror"
    MISTERIO = "misterio"
    ROMANCE = "romance"
    HISTORICO = "historico"
    AVENTURA = "aventura"
    COMEDIA = "comedia"
    DRAMA = "drama"
    BIOGRAFICO = "biografico"
    ENSAYO = "ensayo"
    
class FormatDownload(str, Enum):
    """Formatos de descarga disponibles para los libros."""

    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "markdown"
    
class BookInitRequest(BaseModel):
    """Modelo para la solicitud inicial del libro."""

    id: Optional[str] = Field(None, description="ID único del libro")
    title: str = Field(..., description="Título del libro")
    synopsis: str = Field(..., description="Sinopsis del libro")
    book_style: BookStyle = Field(..., description="Estilo del libro")
    pages: int = Field(..., description="Número de páginas del libro")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "El misterio de la casa abandonada",
                "synopsis": "Una historia de misterio y aventura en una casa antigua.",
                "book_style": BookStyle.MISTERIO,
                "pages": 300,
            }
        }
    }
    


class BookChapter(BaseModel):
    """Modelo para representar un capítulo del libro."""

    id: str = Field(..., description="ID único del capítulo")
    title: str = Field(..., description="Título del capítulo")
    description: str = Field(..., description="Descripción del capítulo")
    content: Optional[str] = Field(None, description="Contenido del capítulo")


class BookIndex(BaseModel):
    """Modelo para representar el índice del libro."""

    chapters: List[BookChapter] = Field(
        default_factory=list, description="Lista de capítulos"
    )


class Book(BaseModel):
    """Modelo para representar un libro completo."""

    id: Optional[str] = Field(None, description="ID único del libro")
    title: str = Field(..., description="Título del libro")
    synopsis: str = Field(..., description="Sinopsis del libro")
    book_style: BookStyle = Field(..., description="Estilo del libro")
    pages: int = Field(..., description="Número de páginas del libro")
    processed_chapters: List[str] = Field(
        default_factory=list, description="Lista de capítulos procesados"
    )
    index: Dict = Field(..., description="Índice del libro")
    created_at: str = Field(..., description="Fecha de creación")
    updated_at: str = Field(..., description="Fecha de última actualización")
    is_completed: bool = Field(
        default=False, description="Indica si el libro está completo"
    )


class ChapterGenerationRequest(BaseModel):
    """Modelo para solicitar la generación de un capítulo."""

    book_id: str = Field(..., description="ID del libro")
    chapter_id: str = Field(..., description="ID del capítulo")


class DownloadBookRequest(BaseModel):
    """Modelo para solicitar la descarga de un libro."""

    book_id: str = Field(..., description="ID del libro")
    format: FormatDownload = Field(..., description="Formato de descarga (ej. PDF, EPUB)")

