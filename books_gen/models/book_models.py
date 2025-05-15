"""
Modelos de datos para la aplicación.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class BookInitRequest(BaseModel):
    """Modelo para la solicitud inicial del libro."""

    title: str = Field(..., description="Título del libro")
    synopsis: str = Field(..., description="Sinopsis del libro")


class BookChapter(BaseModel):
    """Modelo para representar un capítulo del libro."""

    id: str = Field(..., description="ID único del capítulo")
    title: str = Field(..., description="Título del capítulo")
    content: Optional[str] = Field(None, description="Contenido del capítulo")


class BookIndex(BaseModel):
    """Modelo para representar el índice del libro."""

    chapters: List[BookChapter] = Field(
        default_factory=list, description="Lista de capítulos"
    )


class Book(BaseModel):
    """Modelo para representar un libro completo."""

    id: str = Field(..., description="ID único del libro")
    title: str = Field(..., description="Título del libro")
    synopsis: str = Field(..., description="Sinopsis del libro")
    index: BookIndex = Field(default_factory=BookIndex, description="Índice del libro")
    created_at: str = Field(..., description="Fecha de creación")
    updated_at: str = Field(..., description="Fecha de última actualización")


class ChapterGenerationRequest(BaseModel):
    """Modelo para solicitar la generación de un capítulo."""

    book_id: str = Field(..., description="ID del libro")
    chapter_id: str = Field(..., description="ID del capítulo")
