"""
Aplicación principal para ejecutar el servidor API.
"""
import uvicorn
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .api.api import app as api_app

# Crear la aplicación CLI
cli = typer.Typer(help="Generador de libros usando LLMs")
console = Console()


@cli.command()
def run(
    host: str = typer.Option("127.0.0.1", help="Dirección IP del servidor"),
    port: int = typer.Option(8000, help="Puerto del servidor"),
    reload: bool = typer.Option(False, help="Recargar automáticamente el servidor"),
):
    """
    Inicia el servidor API.
    """
    console.print(
        Panel(
            Text.from_markup(
                f"🚀 [bold green]Iniciando servidor API del Generador de Libros[/bold green]\n"
                f"💻 [bold]Dirección:[/bold] [cyan]http://{host}:{port}[/cyan]\n"
                f"📘 [bold]Documentación API:[/bold] [cyan]http://{host}:{port}/docs[/cyan]"
            ),
            title="Generador de Libros",
            border_style="green",
        )
    )

    uvicorn.run("books_gen.api.routes:app", host=host, port=port, reload=reload)


def main():
    """
    Función principal para ejecutar la aplicación.
    """
    cli()


if __name__ == "__main__":
    main()
