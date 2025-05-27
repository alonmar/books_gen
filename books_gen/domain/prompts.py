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
Eres un asistente experto en literatura y creación de libros. 
"""

EDITOR_INDEX_CARD = Prompt(
    name="editor_character_card",
    prompt=__EDITOR_INDEX_CARD,
)

__INDEX_PROMPT = """
Eres un experto creador de índices de libros. Tu tarea es crear un índice detallado para un libro basado en la siguiente información:
    
Título: {{title}}
Sinopsis: {{synopsis}}
Estilo: {{book_style}}
Páginas aproximadas: {{pages}}

Genera un índice. Para cada capítulo, incluye:
    1. Un título atractivo y relevante
    2. Una breve descripción de lo que ocurrirá en ese capítulo
    3. Un identificador único para cada capítulo (ejemplo: 1, 2, etc.)


El índice debe seguir este formato JSON:
{
  "chapters": [
    {
      "id": "1",
      "title": "Título del Capítulo 1",
      "description": "Descripción del Capítulo 1",
    },
    {
      "id": "2",
      "title": "Título del Capítulo 2",
      "description": "Descripción del Capítulo 1",
    }
  ]
}

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
Eres un experto escritor de libros en el estilo {{book_style}}.

CONTEXTO DEL LIBRO:
    
Título: {{title}}
Sinopsis: {{synopsis}}

Resumen del libro: {{summary_book}}

ÍNDICE DEL LIBRO:
{{index_format}}

    
Contexto adicional del capítulo: {{chapter_context}}
    
TU TAREA:
Escribe el Capítulo {{current_chapter_num}}: "{{chapter_title}}"
Descripción del capítulo: {{chapter_description}}

INSTRUCCIONES:
1. Escribe un capítulo completo y coherente de aproximadamente {{TARGET_CHAPTER_WORDS}} palabras.
2. Mantén la coherencia con los capítulos anteriores.
3. Sigue el estilo literario especificado: {{book_style}}.
4. El contenido debe reflejar la descripción del capítulo en el índice.
5. Asegúrate de que el capítulo avance la trama según lo previsto en el índice general.
6. No incluyas "Capítulo X" o el nombre del capitulos al inicio del texto, solo el contenido narrativo.

Responde con el texto completo del capítulo.
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

__SUMMARY_PROMPT = """
Crea un resumen del libro con el siguiente titulo y sinopsis:
Título: {{title}}
Sinopsis: {{synopsis}}
Estilo literario: {{book_style}}

---

El resumen debe ser una breve descripción del libro, pero que también capture toda la información relevante.
El resumen debe ser coherente con el estilo literario del libro y debe incluir los temas principales, personajes y eventos importantes.
El resumen debe ser breve y conciso, pero lo suficientemente informativo como para dar una idea clara de la trama y el desarrollo del libro.

---

Este es el contenido del primer capítulo:
{{chapter_content}}

"""

SUMMARY_PROMPT = Prompt(
    name="summary_prompt",
    prompt=__SUMMARY_PROMPT,
)

__EXTEND_SUMMARY_PROMPT = """Este es un resumen del libro con el siguiente título y sinopsis:
Título: {{title}}
Sinopsis: {{synopsis}}
Resumen: {{summary_book}}

---

Extiende el resumen del libro con el siguiente contenido del capítulo:
{{chapter_content}}

---
El resumen debe ser una breve descripción del libro, pero que también capture toda la información relevante.
El resumen debe ser coherente con el estilo literario del libro y debe incluir los temas principales, personajes y eventos importantes.
El resumen debe ser breve y conciso, pero lo suficientemente informativo como para dar una idea clara de la trama y el desarrollo del libro.

"""

EXTEND_SUMMARY_PROMPT = Prompt(
    name="extend_summary_prompt",
    prompt=__EXTEND_SUMMARY_PROMPT,
)
