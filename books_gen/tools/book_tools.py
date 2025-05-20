"""
Herramientas específicas para la generación de contenido de libros.
"""
from typing import Dict, List, Optional
import json
import os
import uuid
from datetime import datetime
from langchain.tools import tool

from ..models.book_models import Book, BookIndex, BookChapter, BookStyle
from books_gen.config import settings


def _get_book_path(book_id: str) -> str:
    """Obtiene la ruta del archivo del libro."""
    return os.path.join(settings.BOOKS_DIR, f"{book_id}.json")


def _get_book_index_without_content(book_id: str) -> Book:
    """Obtiene el índice del libro."""
    book_path = _get_book_path(book_id)
    if not os.path.exists(book_path):
        return None

    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    for chapter in book_data["index"]["chapters"]:
        # Eliminar el contenido del capítulo si existe
        if chapter.get("content"):
            del chapter["content"]
    
    
    book = Book(
        id=book_data["id"],
        title=book_data["title"],
        synopsis=book_data["synopsis"],
        book_style=BookStyle(book_data["book_style"]),
        processed_chapters=book_data["processed_chapters"],
        pages=book_data["pages"],
        index=book_data["index"],
        created_at=book_data["created_at"],
        updated_at=book_data["updated_at"],
    )

    return book


@tool
def generate_book_index(title: str, synopsis: str) -> str:
    """
    Genera el índice de un libro basado en el título y la sinopsis.

    Args:
        title: El título del libro
        synopsis: La sinopsis del libro

    Returns:
        Una representación en texto del índice generado
    """
    # En una implementación real, aquí se utilizaría el LLM de Groq
    # Por ahora, generamos un índice de ejemplo
    book_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    # Crear estructura básica del libro
    book = Book(
        id=book_id, title=title, synopsis=synopsis, created_at=now, updated_at=now
    )

    # Generar capítulos de ejemplo (en la versión real esto lo haría el LLM)
    book.index.chapters = [
        BookChapter(
            id=f"cap_{i}",
            title=f"Capítulo {i}: Título de ejemplo",
            subchapters=[
                {
                    "id": f"subcap_{i}_{j}",
                    "title": f"Subcapítulo {j}: Subtítulo de ejemplo",
                }
                for j in range(1, 4)
            ],
        )
        for i in range(1, 6)
    ]

    # Guardar el libro
    os.makedirs(settings.BOOKS_DIR, exist_ok=True)
    with open(_get_book_path(book_id), "w", encoding="utf-8") as f:
        f.write(book.model_dump_json(indent=2))

    return f"Se generó el índice para el libro '{title}' con ID: {book_id}"


@tool
def list_books() -> str:
    """
    Lista todos los libros disponibles.

    Returns:
        Una lista formateada de los libros disponibles
    """
    if not os.path.exists(settings.BOOKS_DIR):
        return "No hay libros disponibles."

    books = []
    for filename in os.listdir(settings.BOOKS_DIR):
        if filename.endswith(".json"):
            with open(
                os.path.join(settings.BOOKS_DIR, filename), "r", encoding="utf-8"
            ) as f:
                book_data = json.load(f)
                books.append(
                    {
                        "id": book_data["id"],
                        "title": book_data["title"],
                        "synopsis": book_data["synopsis"],
                        "chapters": len(book_data["index"]["chapters"]),
                    }
                )

    if not books:
        return "No hay libros disponibles."

    result = "Libros disponibles:\n"
    for book in books:
        result += f"- ID: {book['id']}, Título: {book['title']}, Capítulos: {book['chapters']}\n"

    return result


@tool
def get_book_index(book_id: str) -> str:
    """
    Obtiene el índice de un libro específico.

    Args:
        book_id: El ID del libro

    Returns:
        Una representación en texto del índice del libro
    """
    book_path = _get_book_path(book_id)
    if not os.path.exists(book_path):
        return f"No se encontró el libro con ID: {book_id}"

    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    result = f"Índice del libro: {book_data['title']}\n\n"

    for i, chapter in enumerate(book_data["index"]["chapters"], 1):
        result += f"{i}. {chapter['title']}\n"
        for j, subchapter in enumerate(chapter.get("subchapters", []), 1):
            result += f"   {i}.{j}. {subchapter['title']}\n"

    return result


@tool
def generate_chapter_content(book_id: str, chapter_id: str) -> str:
    """
    Genera el contenido de un capítulo específico.

    Args:
        book_id: El ID del libro
        chapter_id: El ID del capítulo

    Returns:
        Un mensaje indicando que se generó el contenido
    """
    book_path = _get_book_path(book_id)
    if not os.path.exists(book_path):
        return f"No se encontró el libro con ID: {book_id}"

    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    # Buscar el capítulo
    chapter_found = False
    for chapter in book_data["index"]["chapters"]:
        if chapter["id"] == chapter_id:
            chapter_found = True
            # En una implementación real, aquí se utilizaría el LLM de Groq
            chapter[
                "content"
            ] = f"Este es el contenido generado para el capítulo '{chapter['title']}'. En una implementación real, este contenido sería generado por un modelo de lenguaje avanzado."
            break

    if not chapter_found:
        return f"No se encontró el capítulo con ID: {chapter_id}"

    # Actualizar fecha
    book_data["updated_at"] = datetime.now().isoformat()

    # Guardar el libro actualizado
    with open(book_path, "w", encoding="utf-8") as f:
        json.dump(book_data, f, indent=2)

    return f"Se generó el contenido para el capítulo con ID: {chapter_id}"
