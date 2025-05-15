from loguru import logger


class Prompt:
    def __init__(self, name: str, prompt: str) -> None:
        self.name = name

        # try:
        #    self.__prompt = opik.Prompt(name=name, prompt=prompt)
        # except Exception:
        #    logger.warning(
        #        "Can't use Opik to version the prompt (probably due to missing or invalid credentials). Falling back to local prompt. The prompt is not versioned, but it's still usable."
        #    )
        self.__prompt = prompt

    @property
    def prompt(self) -> str:
        # if isinstance(self.__prompt, opik.Prompt):
        #    return self.__prompt.prompt
        # else:
        #    return self.__prompt
        return self.__prompt

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return self.__str__()


# ===== PROMPTS =====


# --- Index ---

__EDITOR_INDEX_CARD = """
Eres un asistente experto en literatura y creación de libros. Tu tarea es generar un índice
detallado para un libro basado en el título y la sinopsis proporcionados.
Debes tambien incluir una breve descripción de cada capítulo.

El índice debe seguir este formato JSON:
{
  "chapters": [
    {
      "id": "cap_1",
      "title": "Título del Capítulo 1",
      "description": "Descripción del Capítulo 1",
    },
    {
      "id": "cap_2",
      "title": "Título del Capítulo 2",
      "description": "Descripción del Capítulo 1",
    }
  ]
}

Genera entre 5 y 10 capítulos Asegúrate de que los títulos sean creativos, interesantes y 
relevantes para la sinopsis del libro, la description debe de dar una idea de lo que deberia 
de contener el libro y debe de ser coherente con el indice.
"""

EDITOR_INDEX_CARD = Prompt(
    name="editor_character_card",
    prompt=__EDITOR_INDEX_CARD,
)

__INDEX_PROMPT = """
Genera un índice para un libro con la siguiente información:
    
Título: {{title}}
Sinopsis: {{synopsis}}

Responde ÚNICAMENTE con el formato JSON especificado.
"""

INDEX_PROMPT = Prompt(
    name="index_prompt",
    prompt=__INDEX_PROMPT,
)


# --- Chapter generation ---

__EDITOR_CHAPTER_CARD = """
Eres un asistente experto en literatura y creación de libros. Tu tarea es generar el contenido
de un capítulo basado en el título, la sinopsis del libro y una descripcion del capitulo proporcionados.
El contenido debe ser coherente con el índice del libro y la descripción del capítulo.

Nunca comiences diciendo el título del capítulo, ya que ya está incluido en la descripción.
"""

EDITOR_CHAPTER_CARD = Prompt(
    name="editor_chapter_card",
    prompt=__EDITOR_CHAPTER_CARD,
)

__CHAPTER_PROMPT = """
Escribe el contenido para el capítulo "{{chapter_title}}" del libro:
    
Título del libro: {{title}}
Sinopsis del libro: {{synopsis}}
Descripción del capítulo: {{chapter_description}}
index: {{index}}

    
Contexto adicional del capítulo: {{chapter_context}}
    
Escribe el contenido completo del capítulo.
"""

CHAPTER_PROMPT = Prompt(
    name="chapter_prompt",
    prompt=__CHAPTER_PROMPT,
)

__EDITO_CHAPTER_EXTEND_PROMPT = """
Eres un asistente experto en literatura y creación de libros. Tu tarea es seguir redactando el contenido
del capítulo actual. La continuacion debe ser coherente con el índice del libro, la descripción del capítulo y el texto actual del capitulo.
"""

EDITOR_CHAPTER_EXTEND_CARD = Prompt(
    name="editor_chapter_extend_card",
    prompt=__EDITO_CHAPTER_EXTEND_PROMPT,
)


__CHAPTER_EXTEND_PROMPT = """
Continua el contenido del capítulo "{{chapter_title}}" del libro:

Título del libro: {{title}}
Sinopsis del libro: {{synopsis}}
Descripción del capítulo: {{chapter_description}}
index: {{index}}
Texto actual del capítulo: {{current_chapter_content}}

Contexto adicional del capítulo: {{chapter_context}}
"""

CHAPTER_EXTEND_PROMPT = Prompt(
    name="chapter_extend_prompt",
    prompt=__CHAPTER_EXTEND_PROMPT,
)


# --- Summary ---
