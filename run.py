#!/usr/bin/env python
"""
Script principal para ejecutar el generador de libros.
"""
import sys
import os
from pathlib import Path

# Asegurarse de que el directorio raíz esté en el path de Python
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

try:
    from books_gen.main import main
except ImportError as e:
    print(f"Error al importar el módulo principal: {e}")
    print("Es posible que necesites instalar las dependencias primero.")
    print("Ejecuta: pip install -e .")
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
    except Exception as e:
        print(f"Error al ejecutar la aplicación: {e}")
        sys.exit(1)
