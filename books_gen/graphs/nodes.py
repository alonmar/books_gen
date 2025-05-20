import uuid
import os
import json
from datetime import datetime


from books_gen.graphs.state import BookGenerationState
from books_gen.config import settings

from books_gen.models.book_models import Book, BookChapter, BookStyle
from books_gen.tools.book_tools import _get_book_path, _get_book_index_without_content

# from books_gen.tools.llm_client import (
#    generate_book_index_with_llm,
#    generate_chapter_content_with_llm,
#    generate_summarize_resume_with_llm,
# )
from books_gen.graphs.chains import get_book_index_chain, get_chapter_chain, get_chapter_extend_chain


async def initialize_book(state: BookGenerationState):
    """
    Inicializa un nuevo libro con título y sinopsis.
    """
    try:
        # Generar ID único para el libro
        
        if (state.get('book_id') == "") or (state.get('book_id') is None):
            
            book = state['book']
            
            book_id = str(uuid.uuid4())
            book.id = book_id
            
            state['book_id'] = book_id

            
            from pdb import set_trace
            set_trace()

            # Guardar el libro inicial            os.makedirs(settings.BOOKS_DIR, exist_ok=True)
            with open(_get_book_path(book_id), "w", encoding="utf-8") as f:
                f.write(book.model_dump_json(indent=2))
                
                
            
            state['book'] = book
            state['book_id'] = book_id
            state['title'] = book.title
            state['synopsis'] = book.synopsis
            state['book_style'] = book.book_style
            state['pages'] = book.pages
            
                
            return state
        else:
            # Si el libro ya tiene ID, simplemente lo retornamos
            book_id = state.get('book_id', "")

            book = _get_book_index_without_content(book_id)
            
            
            state['book'] = book
            state['book_id'] = book_id
            state['title'] = book.title
            state['synopsis'] = book.synopsis
            state['book_style'] = book.book_style
            state['pages'] = book.pages
            

            return state

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
                'book_style': state["book_style"],
                "pages": state["pages"],
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
        book = state.get("book")
        
        if not book:
            return {
                **state,
                "error": "No se ha inicializado el libro correctamente",
            }
            
        current_chapter = state.get("current_chapter")
        
        

        # Cargar el libro
        book_path = _get_book_path(state["book_id"])
        with open(book_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        # Buscar el capítulo
        chapter_found = False
        chapter_title = ""
        chapter_description = ""
        is_last_chapter = False

        # Extraemos el título y la descripción del capítulo
        
        index = book.index
        chapters = index["chapters"]
        index_format = [f"Capitulo{i+1}, Título: {chapter['title']}/n"  for i, chapter in enumerate(chapters)]
        
        
        # Determinar si este es el último capítulo para darle un cierre adecuado
        for i, chapter in enumerate(chapters):
            if chapter["id"] == current_chapter:
                chapter_found = True
                chapter_title = chapter["title"]
                chapter_description = chapter["description"]
                current_chapter_num = i + 1
                is_last_chapter = (i == len(chapters) - 1)
                break
        
        
        
        if not chapter_found:
            return {
                **state,
                "error": f"No se encontró el capítulo con ID: {current_chapter}",
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

        # Obtener el contenido del capítulo anterior para contexto
        
        previous_chapters_summary = ""
        
        
        completed_chapters = state.get("completed_chapters", []) 
        
        if len(completed_chapters) > 0:
            # Si hay capítulos completados, extraer el contenido del último
            previous_chapters_summary = "RESUMEN DE CAPÍTULOS ANTERIORES:\n"
            for chapter in completed_chapters:
                previous_chapters_summary += f"Capítulo {chapter['id']}: {chapter['title']}\n"
                previous_chapters_summary += f"{chapter['description']}\n\n"
                
      
        # Añadir instrucciones especiales si es el último capítulo
        chapter_context = ""
        if is_last_chapter:
            chapter_context += "\n\nEste es el último capítulo del libro, asegúrate de crear un final satisfactorio que cierre todas las tramas."

        # Generar contenido con LLM
        chapter_chain = get_chapter_chain()

        response = await chapter_chain.ainvoke(
            {
                "title": book.title,
                "synopsis": book.synopsis,
                "book_style": book.book_style,
                "chapter_title": chapter_title,
                "chapter_description": chapter_description,
                "previous_chapters_summary": previous_chapters_summary,
                "index_format": index_format,
                "chapter_context": chapter_context,
                'current_chapter_num': current_chapter_num,
                'TARGET_CHAPTER_WORDS': 250,
            }
        )

        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = response
        
        

        # Actualizar el capítulo en el libro
        for chapter in index["chapters"]:
            if chapter["id"] == current_chapter:
                chapter["content"] = response_text
                break
        # Actualizar fecha
        book.index = index
        book.updated_at = datetime.now().isoformat()
        book.processed_chapters.append(current_chapter)
        
        from pdb import set_trace
        set_trace()
        # Guardar el libro actualizado
        with open(book_path, "w", encoding="utf-8") as f:
            f.write(book.model_dump_json(indent=2))
                
        
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
        chapter_description = ""
        is_last_chapter = False

        chapters = book_data["index"]["chapters"]
        for i, chapter in enumerate(chapters):
            if chapter["id"] == state["current_chapter"]:
                chapter_title = chapter["title"]
                chapter_description = chapter.get("description", "")
                is_last_chapter = (i == len(chapters) - 1)
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

        # Obtener el contenido del capítulo anterior para contexto
        previous_chapter_content = state.get("previous_chapter_content", "")
        chapter_context = ""
        
        # Preparar el contexto usando el capítulo anterior
        if previous_chapter_content and previous_chapter_content != current_content:
            chapter_context = "Contenido del capítulo anterior (para mantener continuidad):\n" + previous_chapter_content[:1500] + "..."
        
        # Añadir instrucciones especiales si es el último capítulo
        if is_last_chapter:
            chapter_context += "\n\nEste es el último capítulo del libro, asegúrate de crear un final satisfactorio que cierre todas las tramas."

        # Generar continuación con LLM
        chapter_extend_chain = get_chapter_extend_chain()

        response = await chapter_extend_chain.ainvoke(
            {
                "title": state["title"],
                "synopsis": state["synopsis"],
                "chapter_title": chapter_title,
                "chapter_description": chapter_description,
                "index": state["index"],
                "current_chapter_content": current_content,
                "chapter_context": chapter_context,
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
    """
    Nodo conector que selecciona el siguiente capítulo a procesar.
    Si no hay capítulo actual, selecciona el primero.
    Si ya hay un capítulo actual, selecciona el siguiente.
    """
    try:
        
        # Inicializar la lista de capítulos procesados si no existe
        book = state.get("book")
        if not book:
            return {
                **state,
                "error": "No se ha inicializado el libro correctamente",
            }
            
        processed_chapters = book.processed_chapters
        
        
        # Si no hay un índice, no podemos hacer nada
        if not book.index.get("chapters"):
            return {
                **state,
                "error": "No hay índice o capítulos para procesar",
            }
        
        chapters = book.index["chapters"]
        current_chapter = state.get("current_chapter")
        
        if not current_chapter and len(processed_chapters) == 0:
            # Si no hay capítulo actual, seleccionamos el primero
            current_chapter = chapters[0]["id"]
            return {
                **state,
                "current_chapter": current_chapter,
            }
        
        
        # Seleccionar el siguiente capítulo no procesado
        next_chapter = None
        for chapter in chapters:
            if chapter["id"] not in processed_chapters:
                next_chapter = chapter["id"]
                break
        
        # Si no hay siguiente capítulo, mantener el actual (por si era el último)
        if next_chapter is None and len(chapters) > 0:
            next_chapter = chapters[-1]["id"]
        
        from pdb import set_trace
        set_trace()
        return {
            **state,
            "current_chapter": next_chapter,
            "processed_chapters": processed_chapters,
        }
    except Exception as e:
        return {**state, "error": f"Error en el nodo conector: {str(e)}"}