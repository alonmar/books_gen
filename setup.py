#!/usr/bin/env python
"""
Script de configuración e instalación para el proyecto books_gen.
"""
import os
import sys
import subprocess
from pathlib import Path
from setuptools import setup, find_packages


def check_python_version():
    """Verifica que la versión de Python sea la adecuada."""
    if sys.version_info < (3, 12):
        print("Error: Se requiere Python 3.12 o superior.")
        print(f"Versión actual: {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)


def create_env_file():
    """Crea el archivo .env si no existe."""
    env_path = Path(".env")

    if not env_path.exists():
        api_key = input(
            "Ingresa tu API Key de Groq (deja vacío para configurar después): "
        )

        with open(env_path, "w") as f:
            f.write(f'GROQ_API_KEY="{api_key}"\n')

        print("Archivo .env creado exitosamente.")
    else:
        print("El archivo .env ya existe. No se ha modificado.")


def create_generated_books_dir():
    """Crea el directorio para los libros generados."""
    books_dir = Path("generated_books")

    if not books_dir.exists():
        books_dir.mkdir()
        print("Directorio 'generated_books' creado exitosamente.")
    else:
        print("El directorio 'generated_books' ya existe.")


def install_dependencies():
    """Instala las dependencias del proyecto."""
    print("Instalando dependencias...")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        print("Dependencias instaladas exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al instalar dependencias: {e}")
        sys.exit(1)


def run_setup():
    """Ejecuta la configuración interactiva."""
    print("=== Configurando Books Gen - Generador de Libros con IA ===\n")

    check_python_version()
    create_env_file()
    create_generated_books_dir()

    print("\n=== Configuración completada exitosamente ===")
    print("Para iniciar el servidor, ejecuta: python run.py")


# Configuración setuptools para instalar como paquete
setup(
    name="books-gen",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "langgraph>=0.0.19",
        "langchain>=0.1.0",
        "langchain-groq>=0.1.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.4.2",
        "python-dotenv>=1.0.0",
        "typer>=0.9.0",
        "rich>=13.6.0",
    ],
    entry_points={
        "console_scripts": [
            "books-gen=books_gen.main:main",
        ],
    },
    python_requires=">=3.12",
    description="Generador de libros usando LLMs, LangGraph y Groq",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Si se ejecuta directamente sin argumentos, ejecutar la configuración interactiva
        run_setup()
    else:
        # Si hay argumentos, es setuptools ejecutando la instalación
        pass  # setuptools ya ejecutará la configuración definida arriba
