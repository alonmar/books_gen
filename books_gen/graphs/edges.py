from books_gen.tools.book_tools import _get_book_path
from books_gen.graphs.state import BookGenerationState
import json
from books_gen.models.book_models import BookIndex


def should_end(state: BookGenerationState) -> str:
    """
    Determina si el proceso debe terminar debido a un error.
    """
    if state.get("error"):
        return "error"
    return "continue"


def check_index_exists(state: BookGenerationState) -> str:
    """
    Determina si el libro ya tiene un índice creado.

    Returns:
        str: "exists" si el índice ya existe, "not_exists" si no existe.
    """
    # Verificar si el índice está vacío

    book = state.get("book")

    if not book:
        return "not_exists"
    else:
        index = book.index

    if index and isinstance(index, dict) and index.get("chapters"):
        return "exists"
    return "not_exists"


def check_chapter_content(state: BookGenerationState) -> str:
    """
    Verifica si el capítulo seleccionado ya tiene contenido.

    Returns:
        str: "has_content" si el capítulo ya tiene contenido, "no_content" si está vacío.
    """
    # Si no hay capítulo seleccionado, no podemos verificar contenido
    if not state.get("current_chapter"):
        return "no_content"

    # Verificar si ya hay contenido generado para este capítulo
    generated_content = state["book"].processed_chapters
    if not generated_content:
        return "no_content"
    # Verificar si el capítulo actual ya tiene contenido generado
    if state["current_chapter"] in generated_content:
        return "has_content"

    # Si no hay en el estado, verificar en el archivo
    try:
        book_path = _get_book_path(state["book_id"])
        with open(book_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        for chapter in book_data["index"].get("chapters", []):
            if chapter["id"] == state["current_chapter"] and chapter.get("content"):
                return "has_content"
    except Exception:
        pass

    return "no_content"


def should_summarize_conversation(state: BookGenerationState) -> str:
    """
    Verifica si se debe resumir la conversación.

    Returns:
        str: "summarize" si se debe resumir, "no_summarize" si no.
    """
    # Aquí puedes implementar la lógica para decidir si resumir o no
    # Por ejemplo, podrías verificar el tamaño de la conversación
    if len(state["messages"][-1].content) > 1000:
        return "summarize"
    return "no_summarize"


def should_process_next_chapter(state: BookGenerationState) -> str:
    """
    Determina si hay más capítulos por procesar en el libro.

    Returns:
        str: "next_chapter" si hay más capítulos por procesar, "finish" si se han procesado todos.
    """

    # Si hay un error, terminamos
    if state.get("error"):
        return "finish"

    book = state.get("book")
    if not book:
        return "finish"
    # Verificar que hay un índice
    if (not book.index) or (not book.index.get("chapters")):
        return "finish"

    # Obtener la lista de capítulos
    chapters = book.index.get("chapters")

    # Si no hay capítulos, terminar
    if not chapters:
        return "finish"

    # Determinar el capítulo actual y el siguiente
    processed_chapters = book.processed_chapters

    if len(processed_chapters) == len(chapters):
        # Si todos los capítulos han sido procesados, terminar
        book.is_completed = True
        return "finish"
    else:
        return "next_chapter"
