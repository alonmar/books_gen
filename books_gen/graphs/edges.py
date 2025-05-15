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

    if (
        state["index"]
        and isinstance(state["index"], dict)
        and state["index"].get("chapters")
    ):
        return "exists"
    return "not_exists"


def check_chapter_content(state: BookGenerationState) -> str:
    """
    Verifica si el capítulo seleccionado ya tiene contenido.

    Returns:
        str: "has_content" si el capítulo ya tiene contenido, "no_content" si está vacío.
    """
    # Si no hay capítulo seleccionado, no podemos verificar contenido
    if not state["current_chapter"]:
        return "no_content"

    # Verificar si ya hay contenido generado para este capítulo
    generated_content = state.get("generated_content", {})
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



