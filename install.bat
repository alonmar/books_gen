@echo off
:: Script de instalación para Books Gen en Windows
echo ==== Instalando Books Gen - Generador de Libros con IA ====
echo.

:: Verificar si Python está instalado
python --version > NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python no está instalado o no está en el PATH.
    echo Por favor, instala Python 3.12 o superior desde https://www.python.org/downloads/
    exit /b 1
)

:: Verificar la versión de Python
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set pyver=%%I
for /f "tokens=1,2 delims=." %%A in ("%pyver%") do (
    set pymajor=%%A
    set pyminor=%%B
)

if %pymajor% LSS 3 (
    echo Error: Se requiere Python 3.12 o superior.
    echo Versión detectada: %pyver%
    exit /b 1
)

if %pymajor% EQU 3 (
    if %pyminor% LSS 12 (
        echo Error: Se requiere Python 3.12 o superior.
        echo Versión detectada: %pyver%
        exit /b 1
    )
)

echo Instalando dependencias...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo Error al instalar las dependencias.
    exit /b 1
)

echo.
echo === Configuración básica ===
python setup.py

echo.
echo === Instalación completada exitosamente ===
echo.
echo Para iniciar el servidor, ejecuta: python run.py
