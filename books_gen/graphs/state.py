from langgraph.graph import MessagesState
from typing import List, Union, Optional
from books_gen.models.book_models import Book, BookStyle, BookChapter


# Definimos los estados para nuestro grafo
class BookGenerationState(MessagesState):
    """Estado para el proceso de generación de libro."""

    book: Book
    book_id: Optional[str]
    title: str
    synopsis: str
    book_style: BookStyle
    pages: int
    current_chapter: str
    generated_content: dict
    previous_chapter_content: str
    is_last_chapter: bool
    error: str
    summary_book: str
