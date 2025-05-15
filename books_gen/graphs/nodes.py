import uuid
import os
import json
from datetime import datetime


from books_gen.graphs.state import BookGenerationState
from books_gen.config import settings

from books_gen.models.book_models import Book
from books_gen.tools.book_tools import _get_book_path, _get_book_index_without_content

# from books_gen.tools.llm_client import (
#    generate_book_index_with_llm,
#    generate_chapter_content_with_llm,
#    generate_summarize_resume_with_llm,
# )
from books_gen.graphs.chains import get_book_index_chain, get_chapter_chain, get_chapter_extend_chain


async def initialize_book(state: BookGenerationState) -> BookGenerationState:
    """
    Inicializa un nuevo libro con título y sinopsis.
    """

    try:
        # Generar ID único para el libro
        if (state["book_id"] == "") or (state["book_id"] is None):
            book_id = str(uuid.uuid4())

            now = datetime.now().isoformat()

            # Crear estructura básica del libro
            book = Book(
                id=book_id,
                title=state["title"],
                synopsis=state["synopsis"],
                created_at=now,
                updated_at=now,
            )

            # Guardar el libro inicial

            os.makedirs(settings.BOOKS_DIR, exist_ok=True)
            with open(_get_book_path(book_id), "w", encoding="utf-8") as f:
                f.write(book.model_dump_json(indent=2))

            return {
                **state,
                "book_id": book_id,
                "index": {},
                "current_chapter": "",
                "generated_content": {},
                "error": "",
            }
        else:
            # Si el libro ya tiene ID, simplemente lo retornamos

            index = _get_book_index_without_content(state["book_id"])

            return {
                **state,
                "index": index,
            }

    except Exception as e:
        return {**state, "error": f"Error al inicializar el libro: {str(e)}"}


async def generate_index(state: BookGenerationState) -> BookGenerationState:
    """
    Genera el índice del libro utilizando el LLM.
    """
    try:
        index_chain = get_book_index_chain()
        # Generar índice con LLM
        response = await index_chain.ainvoke(
            {
                "title": state["title"],
                "synopsis": state["synopsis"],
            }
        )

        if hasattr(response, "content"):
            response_text = response.content

        else:
            response_text = response

        # Intentar parsear el JSON del índice
        try:
            index_dict = json.loads(response_text)
        except json.JSONDecodeError:
            # Si no es JSON válido, intentar extraer solo la parte JSON
            import re

            json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
            if json_match:
                response = json_match.group(1)
                index_dict = json.loads(response)
            else:
                raise ValueError(
                    "No se pudo extraer un JSON válido de la respuesta del LLM"
                )

        # Cargar el libro existente
        book_path = _get_book_path(state["book_id"])
        with open(book_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        # Actualizar el índice
        book_data["index"] = index_dict
        book_data["updated_at"] = datetime.now().isoformat()

        # Guardar el libro actualizado
        with open(book_path, "w", encoding="utf-8") as f:
            json.dump(book_data, f, indent=2)

        return {**state, "index": index_dict, "error": ""}
    except Exception as e:
        return {**state, "error": f"Error al generar el índice: {str(e)}"}


async def generate_chapter(state: BookGenerationState) -> BookGenerationState:
    """
    Genera el contenido de un capítulo específico utilizando el LLM.
    """
    try:
        # Verificar que se haya seleccionado un capítulo
        if not state["current_chapter"]:
            return {
                **state,
                "error": "No se ha seleccionado ningún capítulo para generar",
            }

        # Cargar el libro
        book_path = _get_book_path(state["book_id"])
        with open(book_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        # Buscar el capítulo
        chapter_found = False
        chapter_title = ""
        chapter_context = ""

        # extremos el titulo y la descripcion del capitulo
        # TODO: el libro se puede cargar desde la llamada en el endpoint
        # TODO: cargar desde la base de datos

        index = state["index"]

        for chapter in index["chapters"]:
            if chapter["id"] == state["current_chapter"]:
                chapter_found = True
                chapter_title = chapter["title"]
                chapter_description = chapter["description"]
                break

        if not chapter_found:
            return {
                **state,
                "error": f"No se encontró el capítulo con ID: {state['current_chapter']}",
            }
        if not chapter_title:
            return {
                **state,
                "error": "El capítulo seleccionado no tiene título",
            }
        if not chapter_description:
            return {
                **state,
                "error": "El capítulo seleccionado no tiene descripción",
            }

        # Generar contenido con LLM
        chapter_chain = get_chapter_chain()

        response = await chapter_chain.ainvoke(
            {
                "title": state["title"],
                "synopsis": state["synopsis"],
                "chapter_title": chapter_title,
                "chapter_description": chapter_description,
                "index": index,
                "chapter_context": "",
            }
        )

        if hasattr(response, "content"):
            response_text = response.content

        else:
            response_text = response

        # Actualizar el capítulo en el libro
        for chapter in index["chapters"]:
            if chapter["id"] == state["current_chapter"]:
                chapter["content"] = response_text
                break

        # Actualizar fecha
        book_data["index"] = index
        book_data["updated_at"] = datetime.now().isoformat()

        # Guardar el libro actualizado
        with open(book_path, "w", encoding="utf-8") as f:
            json.dump(book_data, f, indent=2)

        return {
            **state,
            "error": "",
        }
    except Exception as e:
        return {**state, "error": f"Error al generar el capítulo: {str(e)}"}


async def continue_chapter_generation(
    state: BookGenerationState
) -> BookGenerationState:
    """
    Continúa la generación de un capítulo existente utilizando el texto final como contexto.
    """
    try:
        # Verificar que se haya seleccionado un capítulo
        if not state["current_chapter"]:
            return {
                **state,
                "error": "No se ha seleccionado ningún capítulo para continuar generando",
            }

        # Cargar el libro
        book_path = _get_book_path(state["book_id"])
        with open(book_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        # Buscar el capítulo y extraer contenido existente
        current_content = ""
        chapter_title = ""

        for chapter in book_data["index"]["chapters"]:
            if chapter["id"] == state["current_chapter"]:
                chapter_title = chapter["title"]
                if "content" in chapter and chapter["content"]:
                    current_content = chapter["content"]
                break

        if not chapter_title:
            return {
                **state,
                "error": f"No se encontró el capítulo con ID: {state['current_chapter']}",
            }

        if not current_content:
            return {
                **state,
                "error": "El capítulo seleccionado no tiene contenido para continuar",
            }

        # Generar continuación con LLM

        chapter_extend_chain = get_chapter_extend_chain()

        response = await chapter_extend_chain.ainvoke(
            {
                "title": state["title"],
                "synopsis": state["synopsis"],
                "chapter_title": chapter_title,
                "chapter_description": chapter["description"],
                "index": state["index"],
                "current_chapter_content": current_content,
                "chapter_context": "",
            }
        )

        if hasattr(response, "content"):
            continuation = response.content

        else:
            continuation = response

        # Actualizar el contenido del capítulo añadiendo la continuación
        new_content = current_content + "\n\n" + continuation

        # Actualizar el capítulo en el libro
        for chapter in book_data["index"]["chapters"]:
            if chapter["id"] == state["current_chapter"]:
                chapter["content"] = new_content
                break

        # Actualizar fecha
        book_data["updated_at"] = datetime.now().isoformat()

        # Guardar el libro actualizado
        with open(book_path, "w", encoding="utf-8") as f:
            json.dump(book_data, f, indent=2)

        return {
            **state,
            'index': book_data["index"],
            "error": "",
        }
    except Exception as e:
        return {**state, "error": f"Error al continuar el capítulo: {str(e)}"}


async def connector_node(state: BookGenerationState):
    return {}