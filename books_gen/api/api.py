"""
API para la generación de libros.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from langchain.schema import HumanMessage, AIMessage
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from books_gen.models.book_models import BookInitRequest
from books_gen.graphs.graph import create_book_generation_graph
from books_gen.tools.book_tools import _get_book_path
from books_gen.config import settings
from books_gen.graphs.state import BookGenerationState

# Crear la aplicación FastAPI
app = FastAPI(
    title="Generador de Libros API",
    description="API para generar libros utilizando LLMs",
    version="0.1.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, límita esto a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Almacén para los trabajos en segundo plano
background_jobs = {}


def __format_messages(
    messages: Union[str, list[dict[str, Any]]]
) -> list[Union[HumanMessage, AIMessage]]:
    """Convert various message formats to a list of LangChain message objects.

    Args:
        messages: Can be one of:
            - A single string message
            - A list of string messages
            - A list of dictionaries with 'role' and 'content' keys

    Returns:
        list[Union[HumanMessage, AIMessage]]: A list of LangChain message objects
    """

    if isinstance(messages, str):
        return [HumanMessage(content=messages)]

    if isinstance(messages, list):
        if not messages:
            return []

        if (
            isinstance(messages[0], dict)
            and "role" in messages[0]
            and "content" in messages[0]
        ):
            result = []
            for msg in messages:
                if msg["role"] == "user":
                    result.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    result.append(AIMessage(content=msg["content"]))
            return result

        return [HumanMessage(content=message) for message in messages]

    return []


@app.get("/")
def read_root():
    """
    Endpoint de bienvenida que sirve la página principal.
    """
    index_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "static", "index.html"
    )
    return FileResponse(index_path)


@app.get("/books")
def list_books():
    """
    Lista todos los libros disponibles.
    """
    if not os.path.exists(settings.BOOKS_DIR):
        return []

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
                        "created_at": book_data["created_at"],
                        "updated_at": book_data["updated_at"],
                    }
                )

    return books


@app.get("/books/{book_id}")
def get_book(book_id: str):
    """
    Obtiene los detalles de un libro específico.
    """
    book_path = _get_book_path(book_id)
    if not os.path.exists(book_path):
        raise HTTPException(status_code=404, detail=f"Libro no encontrado: {book_id}")

    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    return book_data


@app.post("/books")
async def create_book(request: BookInitRequest, background_tasks: BackgroundTasks):
    """
    Crea un nuevo libro e inicia el proceso de generación de índice.
    """
    # Crear el grafo
    book_graph = create_book_generation_graph()
    # Compilar el grafo
    book_app = book_graph.compile()

    # ID único para el trabajo
    job_id = str(uuid.uuid4())

    # Configurar el estado inicial
    # initial_state = {
    #    "book_id": "",
    #    "title": request.title,
    #    "synopsis": request.synopsis,
    #    "index": {},
    #    "current_chapter": "",
    #    "generated_content": {},
    #    "error": "",
    # }
    initial_state_book = BookGenerationState(
        messages=__format_messages(""),
        book_id="",
        title=request.title,
        synopsis=request.synopsis,
        index={},
        current_chapter="",
        generated_content={},
        error="",
    )

    # Ejecutar el grafo en segundo plano hasta el punto de generación del índice
    async def run_graph_task():
        try:
            # Inicializar y generar el índice
            output_state = await book_app.ainvoke(
                input={
                    "book_id": initial_state_book["book_id"],
                    "title": initial_state_book["title"],
                    "synopsis": initial_state_book["synopsis"],
                },
            )
            # last_message = output_state["messages"][-1]
            print(f"Estado de salida: {output_state}")

            background_jobs[job_id] = {
                "status": "completed" if not output_state.get("error") else "error",
                "error": output_state.get("error", ""),
                "book_id": output_state.get("book_id", ""),
                "completed_at": datetime.now().isoformat(),
            }

            return output_state

        except Exception as e:
            background_jobs[job_id] = {
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now().isoformat(),
            }

    # Iniciar la tarea en segundo plano
    background_tasks.add_task(run_graph_task)

    # Registrar el trabajo
    background_jobs[job_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
    }

    return {
        "job_id": job_id,
        "title": request.title,
        "message": "Proceso de generación de índice iniciado",
    }


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Obtiene el estado de un trabajo en segundo plano.
    """
    if job_id not in background_jobs:
        raise HTTPException(status_code=404, detail=f"Trabajo no encontrado: {job_id}")

    return background_jobs[job_id]


@app.post("/books/{book_id}/chapters/{chapter_id}")
async def generate_chapter(
    book_id: str, chapter_id: str, background_tasks: BackgroundTasks
):
    """
    Genera el contenido para un capítulo específico.
    """
    # Verificar que el libro existe
    book_path = _get_book_path(book_id)
    if not os.path.exists(book_path):
        raise HTTPException(status_code=404, detail=f"Libro no encontrado: {book_id}")

    # Cargar el libro para verificar el capítulo
    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    # Verificar que el capítulo existe
    chapter_found = False
    for chapter in book_data["index"]["chapters"]:
        if chapter["id"] == chapter_id:
            chapter_found = True
            break

    if not chapter_found:
        raise HTTPException(
            status_code=404, detail=f"Capítulo no encontrado: {chapter_id}"
        )

    # Crear el grafo para la generación de capítulos
    book_graph = create_book_generation_graph()
    book_app = book_graph.compile()

    # ID único para el trabajo
    job_id = str(uuid.uuid4())

    # Configurar el estado inicial para la generación del capítulo
    initial_state_book = {
        "book_id": book_id,
        "title": book_data["title"],
        "synopsis": book_data["synopsis"],
        "index": book_data["index"],
        "current_chapter": chapter_id,
        "generated_content": {},
        "error": "",
    }

    # Ejecutar el grafo en segundo plano solo para la generación del capítulo
    async def run_chapter_generation():
        try:
            # Saltamos la inicialización y generación de índice, vamos directo a generar el capítulo
            # Filtramos para quedarnos solo con el nodo de generación de capítulos
            final_state = await book_app.ainvoke(
                input={
                    "book_id": initial_state_book["book_id"],
                    "title": initial_state_book["title"],
                    "synopsis": initial_state_book["synopsis"],
                    "index": initial_state_book["index"],
                    "current_chapter": initial_state_book["current_chapter"],
                },
            )

            # Obtener el estado final
            background_jobs[job_id] = {
                "status": "completed" if not final_state.get("error") else "error",
                "error": final_state.get("error", ""),
                "book_id": book_id,
                "chapter_id": chapter_id,
                "completed_at": datetime.now().isoformat(),
            }

            print(f"Estado de salida: {final_state}")

        except Exception as e:
            background_jobs[job_id] = {
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now().isoformat(),
            }

    # Iniciar la tarea en segundo plano
    background_tasks.add_task(run_chapter_generation)

    # Registrar el trabajo
    background_jobs[job_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "book_id": book_id,
        "chapter_id": chapter_id,
    }

    return {
        "job_id": job_id,
        "book_id": book_id,
        "chapter_id": chapter_id,
        "message": "Proceso de generación de capítulo iniciado",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("books_gen.api.routes:app", host="0.0.0.0", port=8000, reload=True)
