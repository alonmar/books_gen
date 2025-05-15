#!/bin/bash
# Script de instalación para Books Gen en Linux/macOS

echo "==== Instalando Books Gen - Generador de Libros con IA ===="
echo

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python no está instalado."
    echo "Por favor, instala Python 3.12 o superior desde https://www.python.org/downloads/"
    exit 1
fi

# Verificar la versión de Python
PYVER=$(python3 --version 2>&1 | awk '{print $2}')
PYMAJOR=$(echo $PYVER | cut -d. -f1)
PYMINOR=$(echo $PYVER | cut -d. -f2)

if [ "$PYMAJOR" -lt 3 ] || ([ "$PYMAJOR" -eq 3 ] && [ "$PYMINOR" -lt 12 ]); then
    echo "Error: Se requiere Python 3.12 o superior."
    echo "Versión detectada: $PYVER"
    exit 1
fi

echo "Instalando dependencias..."
pip3 install -e .
if [ $? -ne 0 ]; then
    echo "Error al instalar las dependencias."
    exit 1
fi

echo
echo "=== Configuración básica ==="
python3 setup.py

echo
echo "=== Instalación completada exitosamente ==="
echo
echo "Para iniciar el servidor, ejecuta: python3 run.py"
