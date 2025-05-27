# Books Gen - Generador de Libros con IA

Este proyecto utiliza modelos de lenguaje avanzados (LLMs) a través de la API de Groq, junto con flujos de trabajo de LangGraph y herramientas personalizadas, para generar libros completos de manera interactiva.

## Características

- **Generación de índices**: Crea automáticamente un índice estructurado para tu libro basado en un título y sinopsis.
- **Generación de capítulos**: Genera el contenido detallado de cada capítulo y subcapítulo.
- **Flujos de trabajo**: Utiliza LangGraph para implementar flujos de trabajo complejos y mantener la coherencia narrativa.
- **API REST**: Interfaz API completa para integrar con otras aplicaciones.
- **Interfaz web**: Interfaz sencilla para interactuar con el generador de libros.

## Requisitos

- Python 3.12 o superior
- API Key de Groq

## Instalación

1. Clona este repositorio:

```bash
git clone [url-del-repositorio]
cd books-gen
```

2. Instala las dependencias:

```bash
uv sync
```

3. Configura tu API key de Groq:

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
GROQ_API_KEY="tu-api-key-de-groq"
```

## Uso

### Iniciar el servidor

Para iniciar el servidor API y la interfaz web:

```bash
uv run .\books_gen\infrastructure\api\api.py
```

Por defecto, el servidor se ejecutará en `http://127.0.0.1:8000`.

### Cómo usar la aplicación

1. **Crear un nuevo libro**:
   - Ingresa un título y una sinopsis para tu libro.
   - El sistema generará automáticamente un índice con capítulos y subcapítulos.

2. **Ver tus libros**:
   - Consulta la lista de libros que has creado.
   - Selecciona un libro para ver su índice.

3. **Generar contenido**:
   - Selecciona un capítulo específico para generar su contenido.
   - El sistema utilizará el contexto del libro para mantener la coherencia.

## Arquitectura

- **LangGraph**: Para implementar flujos de trabajo de generación de contenido.
- **Groq API**: Para acceder a modelos de lenguaje de alta calidad.
- **FastAPI**: Para la interfaz API REST.
- **Pydantic**: Para la validación de datos y modelos.

## Estructura del Proyecto

```
books_gen/
├── api/            # API REST con FastAPI
├── graphs/         # Flujos de trabajo con LangGraph
├── models/         # Modelos de datos con Pydantic
├── static/         # Archivos estáticos para la interfaz web
└── tools/          # Herramientas para interactuar con LLMs
```

## Licencia

[MIT](LICENSE)