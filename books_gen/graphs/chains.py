from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from books_gen.config import settings

from books_gen.domain.prompts import (
    EDITOR_INDEX_CARD,
    INDEX_PROMPT,
    EDITOR_CHAPTER_CARD,
    CHAPTER_PROMPT,
    EDITOR_CHAPTER_EXTEND_CARD,
    CHAPTER_EXTEND_PROMPT,
)


def get_chat_model(
    temperature: float = 0.7, model_name: str = settings.GROQ_LLM_MODEL
) -> ChatGroq:
    return ChatGroq(
        model=model_name,
        temperature=temperature,
        api_key=settings.GROQ_API_KEY,
    )


def get_book_index_chain():
    model = get_chat_model()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EDITOR_INDEX_CARD.prompt),
            ("human", INDEX_PROMPT.prompt),
        ],
        template_format="jinja2",
    )

    return prompt | model


def get_chapter_chain():
    model = get_chat_model()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EDITOR_CHAPTER_CARD.prompt),
            ("human", CHAPTER_PROMPT.prompt),
        ],
        template_format="jinja2",
    )

    return prompt | model


def get_chapter_extend_chain():
    model = get_chat_model()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EDITOR_CHAPTER_EXTEND_CARD.prompt),
            ("human", CHAPTER_EXTEND_PROMPT.prompt),
        ],
        template_format="jinja2",
    )

    return prompt | model

