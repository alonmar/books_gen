"""
API para la generación de libros.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from langchain.schema import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from books_gen.models.book_models import BookInitRequest, Book, DownloadBookRequest, BookContentRequest
from books_gen.graphs.graph import create_book_generation_graph
from books_gen.tools.book_tools import _get_book_path
from books_gen.config import settings
from books_gen.graphs.state import BookGenerationState
from books_gen.infrastructure.api.utils import convert_markdown_to_download_file

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
app.mount("/infrastructure/static", StaticFiles(directory=static_dir), name="static")

# Almacén para los trabajos en segundo plano
background_jobs = {}


def __format_messages(
    messages: Union[str, list[dict[str, Any]]]
) -> list[Union[HumanMessage, AIMessage]]:
    """Convert various message formats to a list of LangChain message objects."""
    if isinstance(messages, str):
        return [HumanMessage(content=messages)]

    if isinstance(messages, list):
        if not messages:
            return []

        if isinstance(messages[0], dict) and "role" in messages[0] and "content" in messages[0]:
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


@app.post("/books/index")
async def create_book_index(request: BookInitRequest, background_tasks: BackgroundTasks):
    """
    Crea un nuevo libro e inicia el proceso de generación de índice.
    """
    # Crear el grafo
    book_graph = create_book_generation_graph()
    checkpointer = InMemorySaver()
    in_memory_store = InMemoryStore()
    # Compilar el grafo
    book_app = book_graph.compile(checkpointer=checkpointer, store=in_memory_store)

    # ID único para el trabajo
    job_id = str(uuid.uuid4())
    
    if request.id:
        # Verificar si el libro ya existe
        book_path = _get_book_path(request.id)
        if os.path.exists(book_path):
            raise HTTPException(
                status_code=400, detail=f"El libro con ID {request.id} ya existe."
            )
    else:
        book = Book(
        id=None,
        title=request.title,
        synopsis=request.synopsis,
        book_style=request.book_style,
        pages=request.pages,
        processed_chapters=[],
        index={},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    

    # Configurar el estado inicial
    initial_state_book = BookGenerationState(
        messages=__format_messages(""),
        book=book,
        book_id=request.id,
        title=request.title,
        synopsis=request.synopsis,
        book_style=request.book_style,
        pages=request.pages,
        current_chapter="",
        generated_content={},
        previous_chapter_content="",
        error="",
    )
    thread_id = 1
    
    config = {
        "configurable": {"thread_id": thread_id},
            }

    # Ejecutar el grafo en segundo plano hasta el punto de generación del índice
    async def run_graph_task():
        try:
            # Inicializar y generar el índice
            output_state = await book_app.ainvoke(
                input={**initial_state_book},
                config=config
                )
            
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


@app.post("/books/create")
async def create_book(request: BookContentRequest, background_tasks: BackgroundTasks):
    
    """
    Crea un nuevo libro con el contenido proporcionado.
    """
    # Verificar que el libro existe
    book_path = _get_book_path(request.id)
    if not os.path.exists(book_path):
        raise HTTPException(
            status_code=400, detail=f"El libro con ID {request.id} no existe."
        )
        
     # Crear el grafo
    book_graph = create_book_generation_graph()
    checkpointer = InMemorySaver()
    in_memory_store = InMemoryStore()
    # Compilar el grafo
    book_app = book_graph.compile(checkpointer=checkpointer, store=in_memory_store)

    # ID único para el trabajo
    job_id = str(uuid.uuid4())


    thread_id = 1
    
    config = {
        "configurable": {"thread_id": thread_id},
            }

    # Ejecutar el grafo en segundo plano hasta el punto de generación del índice
    async def run_graph_task():
        try:
            # Inicializar y generar el índice
            output_state = await book_app.ainvoke(
                input={
                    'book_id': request.id,
                    },
                config=config
                )
            
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
        "book_id": request.id,
        "message": "Proceso de generación de contenido iniciado",
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
    
    # Obtener estilo y páginas totales
    estilo = book_data.get("estilo", None)
    paginas_totales = book_data.get("paginas_totales", None)
    resumen_general = book_data.get("resumen_general", "")
    
    # Configurar el estado inicial para la generación del capítulo
    initial_state_book = {
        "book_id": book_id,
        "title": book_data["title"],
        "synopsis": book_data["synopsis"],
        "estilo": estilo,
        "paginas_totales": paginas_totales,
        "resumen_general": resumen_general,
        "index": book_data["index"],
        "current_chapter": chapter_id,
        "generated_content": {},
        "processed_chapters": [],
        "previous_chapter_content": "",
        "error": "",
    }

    # Ejecutar el grafo en segundo plano solo para la generación del capítulo
    async def run_chapter_generation():
        try:
            # Saltamos la inicialización y generación de índice, vamos directo a generar el capítulo
            final_state = await book_app.ainvoke({
                "book_id": initial_state_book["book_id"],
                "title": initial_state_book["title"],
                "synopsis": initial_state_book["synopsis"],
                "estilo": initial_state_book["estilo"],
                "paginas_totales": initial_state_book["paginas_totales"],
                "resumen_general": initial_state_book["resumen_general"],
                "index": initial_state_book["index"],
                "current_chapter": initial_state_book["current_chapter"]
            })

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


@app.post("/books/download")
async def download_book(request: DownloadBookRequest):
    """
    Descarga el libro completo en formato seleccionado.
    """
    # Verificar que el libro existe
    
    book_path = _get_book_path(request.book_id)
    if not os.path.exists(book_path):
        raise HTTPException(status_code=404, detail=f"Libro no encontrado: {request.book_id}")

    # Cargar el libro
    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)
        
    book = Book(
        **book_data)
    
    
    file = convert_markdown_to_download_file(book, request.format)

    
    if not file:
        raise HTTPException(status_code=500, detail="Error al convertir el libro a formato descargable")
    return FileResponse(
        file,
        media_type="application/octet-stream",
        filename=f"{book.title}.{request.format.value}",
    )
    
    
    

@app.post("/books/{book_id}/generate-all")
async def generate_all_chapters(
    book_id: str, background_tasks: BackgroundTasks
):
    """
    Genera automáticamente todos los capítulos del libro en secuencia.
    """
    # Verificar que el libro existe
    book_path = _get_book_path(book_id)
    if not os.path.exists(book_path):
        raise HTTPException(status_code=404, detail=f"Libro no encontrado: {book_id}")

    # Cargar el libro
    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    # Crear el grafo para la generación de capítulos
    book_graph = create_book_generation_graph()
    book_app = book_graph.compile()

    # ID único para el trabajo
    job_id = str(uuid.uuid4())

    # Obtener estilo, páginas totales y resumen general
    estilo = book_data.get("estilo", None)
    paginas_totales = book_data.get("paginas_totales", None)
    resumen_general = book_data.get("resumen_general", "")

    # Configurar el estado inicial para la generación completa del libro
    initial_state_book = {
        "book_id": book_id,
        "title": book_data["title"],
        "synopsis": book_data["synopsis"],
        "estilo": estilo,
        "paginas_totales": paginas_totales,
        "resumen_general": resumen_general,
        "index": book_data["index"],
        "current_chapter": "",  # Vacío para que el connector_node seleccione el primer capítulo
        "generated_content": {},
        "processed_chapters": [],
        "previous_chapter_content": "",
        "error": "",
    }

    # Ejecutar el grafo en segundo plano para generar todos los capítulos
    async def run_all_chapters_generation():
        try:
            # Ejecutar el grafo completo para generar todos los capítulos
            final_state = await book_app.ainvoke(initial_state_book)

            # Actualizar el estado del trabajo
            background_jobs[job_id] = {
                "status": "completed" if not final_state.get("error") else "error",
                "error": final_state.get("error", ""),
                "book_id": book_id,
                "completed_at": datetime.now().isoformat(),
                "processed_chapters": final_state.get("processed_chapters", []),
            }

            print(f"Generación completa finalizada. Estado: {final_state.get('error', 'OK')}")

        except Exception as e:
            background_jobs[job_id] = {
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now().isoformat(),
            }
            print(f"Error en la generación completa: {str(e)}")

    # Iniciar la tarea en segundo plano
    background_tasks.add_task(run_all_chapters_generation)

    # Registrar el trabajo
    background_jobs[job_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "book_id": book_id,
        "message": "Generación automática de todos los capítulos iniciada",
    }

    return {
        "job_id": job_id,
        "book_id": book_id,
        "message": "Proceso de generación automática de capítulos iniciado",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("books_gen.infrastructure.api.api:app", host="0.0.0.0", port=8000, reload=True)
