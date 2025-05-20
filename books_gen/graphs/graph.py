"""
Grafo de flujos para la generación de libros utilizando LangGraph.
"""

from langgraph.graph import StateGraph, END, START

from books_gen.graphs.state import BookGenerationState
from books_gen.graphs.edges import (
    should_end,
    check_index_exists,
    check_chapter_content,
    should_process_next_chapter,
    # should_summarize_chapter_content,
)

from books_gen.graphs.nodes import (
    initialize_book,
    generate_index,
    generate_chapter,
    continue_chapter_generation,
    connector_node,
    
)


def create_book_generation_graph() -> StateGraph:
    """
    Crea un grafo de estado para la generación de libros.
    """
    # Crear un nuevo grafo de estado
    workflow = StateGraph(BookGenerationState)

    # Definir los nodos
    workflow.add_node("initialize", initialize_book)
    workflow.add_node("generate_index", generate_index)
    workflow.add_node("connector_node", connector_node)
    workflow.add_node("generate_chapter", generate_chapter)
    workflow.add_node("continue_chapter", continue_chapter_generation)
    #workflow.add_node("summarize_chapter_content", summarize_chapter_content)

    # Definir las transiciones
    #workflow.set_entry_point("initialize")
    workflow.add_edge(START, "initialize")

    # Verificar si existe un índice después de inicializar
    workflow.add_conditional_edges(
        "initialize",
        check_index_exists,
        {"exists": "connector_node", "not_exists": "generate_index"},
    )

    # Después de generar el índice, ir al nodo conector para empezar a procesar capítulos
    # TODO: Cambiar a un nodo de creacion de capitulo
    workflow.add_edge("generate_index", END)

    # Antes de generar un capítulo, verificar si ya tiene contenido
    workflow.add_conditional_edges(
        "connector_node",
        check_chapter_content,
        {"has_content": "continue_chapter", "no_content": "generate_chapter"},
    )

    # Después de generar un capítulo, verificar si hay error
    workflow.add_conditional_edges(
        "generate_chapter", 
        should_end, 
        {
            "error": END, 
            "continue": "next_chapter_check"
        }
    )

    # Después de continuar un capítulo, verificar si hay error
    workflow.add_conditional_edges(
        "continue_chapter", 
        should_end, 
        {
            "error": END, 
            "continue": "next_chapter_check"
        }
    )
      # Nodo virtual para verificar si hay más capítulos por procesar
    workflow.add_node("next_chapter_check", lambda state: state)
    workflow.add_conditional_edges(
        "next_chapter_check",
        should_process_next_chapter,
        {
            "next_chapter": "connector_node",
            "finish": END
        }
    )

    # workflow.add_conditional_edges(
    #    "connector_node",
    #    should_summarize_chapter_content,
    #    {"summarize": "summarize_chapter_content", "no_summarize": END},
    # )

    return workflow

graph = create_book_generation_graph().compile()

