from langgraph.graph import MessagesState


# Definimos los estados para nuestro grafo
class BookGenerationState(MessagesState):
    """Estado para el proceso de generación de libro."""
    book_id: str
    title: str
    synopsis: str
    index: dict
    current_chapter: str
    generated_content: dict
    error: str
