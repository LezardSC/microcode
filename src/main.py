import argparse
import sys
import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.validation import Validator, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown

from client import LocalLLMClient
from session_manager import SessionManager
from utils.find_session_file import find_session_file

console = Console()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent LLM local en ligne de commande.")

    parser.add_argument(
        "-m", "--model",
        type=str,
        default="qwen3.5:9b",
        help="Le modèle à utiliser (défault: qwen3.5:9b)"
    )
    parser.add_argument(
        "-s", "--sys-prompt",
        type=str,
        default="system_prompt.txt",
        help="Le chemin vers le fichier du system prompt (défaut: system_prompt.txt)"
    )
    parser.add_argument(
        "-u", "--url",
        type=str,
        default="http://localhost:11434/api/chat",
        help="L'URL de l'API Ollama (défault: http://localhost:11434/api/chat)"
    )
    parser.add_argument(
        "-i", "--max-iterations",
        type=int,
        default=15,
        help="Nombre maximum d'itérations pour les outils (défault: 15)"
    )
    parser.add_argument(
        "--disable-thinking",
        action="store_true",
        help="Désactive le mode de réflexion (thinking) du modèle"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liste toutes les sessions sauvegardées",
    )
    parser.add_argument(
        "--resume",
        nargs="?",
        const="LAST",
        default=None,
        help="Chemin vers le fichier JSON pour sauvegarder/charger l'historique. Sans arguments, reprends la dernière session."
    )
    parser.add_argument(
        "--clear",
        type=str,
        help="Supprime une session par son index ou son nom, ou tapez 'all' pour tout supprimer"
    )

    return parser

class NonEmptyValidator(Validator):
    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(
                message="Le message ne peut pas être vide",
                cursor_position=0
            )

def setup_key_bindings() -> KeyBindings:
    """Configure et retourne les raccourcis clavier pour prompt_toolkit."""
    bindings = KeyBindings()

    # Alt + entrée (ou Esc puis Entrée) pour aller à la ligne
    @bindings.add('escape', 'enter')
    def _(event):
        event.current_buffer.insert_text('\n')

    # Entrée pour valider et envoyer
    @bindings.add('enter')
    def _(event):
        event.current_buffer.validate_and_handle()   

    # Ctrl+Z pour Annuler
    @bindings.add('c-z')
    def _(event):
        event.current_buffer.undo()
    
    return bindings

def run_chat(client: LocalLLMClient):
    console.print(Panel(
        "\n[bold cyan]Agent LLM Local démarré[/bold cyan]\nTapez [bold red]'quit'[/bold red] ou [bold red]'exit'[/bold red] pour quitter.",
        border_style="cyan"))

    prompt_session = PromptSession(
        key_bindings=setup_key_bindings(),
        validator=NonEmptyValidator(),
        validate_while_typing=False,
        multiline=True
    )

    while True:
        try:
            content = prompt_session.prompt("\nVous: ")

            if content.lower() in ["quit", "exit"]:
                console.print("\n[bold cyan]End of conversation.[/bold cyan]")
                break

            console.print(f"\n[bold blue]Assistant:[/bold blue]\n")

            stream = client.send_message(content)
            with console.status("[bold green]Le modèle réfléchit...", spinner="dots"):
                first_fragment = next(stream)

            full_response = first_fragment
            with Live(Markdown(""), console=console, refresh_per_second=15) as live:
                for text_fragment in stream:
                    full_response += text_fragment
                    live.update(Markdown(full_response))
            print()

        except requests.exceptions.RequestException as e:
            console.print(f"\n[bold red]Network Error: Can't join the API: {e}[/bold red]")
        except  KeyboardInterrupt:
            console.print("\n[bold cyan]End of conversation.[/bold cyan]")
            return

def create_client(args) -> LocalLLMClient:
    session_file_to_load = None
    if args.resume:
        session_file_to_load = find_session_file(args.resume)
        if not session_file_to_load:
            console.print(f"[bold red]Impossible de trouver une session correspondant à '{args.resume}'[/bold red]")
            sys.exit(1)

    return LocalLLMClient(
        model_name=args.model,
        base_url=args.url,
        sys_prompt_path=args.sys_prompt,
        max_iterations=args.max_iterations,
        disable_thinking=args.disable_thinking,
        session_file=session_file_to_load
    )

def main():
    args = build_parser().parse_args()

    if args.clear:
        SessionManager.clear(args.clear)
        sys.exit(0)

    if args.list:
        SessionManager.list()
        sys.exit(0)

    client = create_client(args)

    run_chat(client)

if __name__ == "__main__":
    main()