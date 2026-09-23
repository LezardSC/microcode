import argparse
import sys
import requests
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown

from client import LocalLLMClient
from config import load_config
from input_prompt import create_prompt_session
from session_manager import SessionManager
from utils.find_session_file import find_session_file

console = Console()

DEFAULT_CONFIG_PATH = "config.toml"

def build_parser(config: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent LLM local en ligne de commande.")

    parser.add_argument(
        "-c", "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Le chemin vers le fichier de configuration TOML (défaut: %(default)s)"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=config["model"]["name"],
        help="Le modèle à utiliser (défaut: %(default)s)"
    )
    parser.add_argument(
        "-s", "--sys-prompt",
        type=str,
        default=config["model"]["system_prompt"],
        help="Le chemin vers le fichier du system prompt (défaut: %(default)s)"
    )
    parser.add_argument(
        "-u", "--url",
        type=str,
        default=config["model"]["url"],
        help="L'URL de l'API Ollama (défaut: %(default)s)"
    )
    parser.add_argument(
        "-i", "--max-iterations",
        type=int,
        default=config["agent"]["max_iterations"],
        help="Nombre maximum d'itérations pour les outils (défaut: %(default)s)"
    )
    parser.add_argument(
        "--disable-thinking",
        action=argparse.BooleanOptionalAction,
        default=config["model"]["disable_thinking"],
        help="Désactive le mode de réflexion (thinking) du modèle (défaut: %(default)s)"
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
        help="Chemin vers le fichier JSON pour sauvegarder/charger l'history. Sans arguments, reprends la dernière session."
    )
    parser.add_argument(
        "--clear",
        type=str,
        help="Supprime une session par son index ou son nom, ou tapez 'all' pour tout supprimer"
    )

    return parser

def run_chat(client: LocalLLMClient, history_dir: str):
    console.print(Panel(
        "\n[bold cyan]Agent LLM Local démarré[/bold cyan]\n"
        "Tapez [bold red]'quit'[/bold red] ou [bold red]'exit'[/bold red] pour quitter "
        "(ou Ctrl+C deux fois sur une saisie vide).",
        border_style="cyan"))

    prompt_session = create_prompt_session(model_name=client.model, history_dir=history_dir)

    while True:
        try:
            console.print()
            console.rule(style="dim")
            content = prompt_session.prompt()

            if content.strip().lower() in ["quit", "exit", "/quit", "/exit"]:
                console.print("\n[bold cyan]End of conversation.[/bold cyan]")
                break

            console.print(f"\n[bold blue]Assistant:[/bold blue]\n")

            stream = client.send_message(content)
            with console.status("[bold green]Le modèle réfléchit...", spinner="dots"):
                first_fragment = next(stream)

            full_response = first_fragment
            with Live(Markdown(full_response), console=console, refresh_per_second=15) as live:
                for text_fragment in stream:
                    full_response += text_fragment
                    live.update(Markdown(full_response))
            print()

        except requests.exceptions.RequestException as e:
            console.print(f"\n[bold red]Network Error: Can't join the API: {e}[/bold red]")
        except  KeyboardInterrupt:
            console.print("\n[bold cyan]End of conversation.[/bold cyan]")
            return

def create_client(args, config: dict) -> LocalLLMClient:
    session_file_to_load = None
    if args.resume:
        session_file_to_load = find_session_file(args.resume, config["paths"]["history_dir"])
        if not session_file_to_load:
            console.print(f"[bold red]Impossible de trouver une session correspondant à '{args.resume}'[/bold red]")
            sys.exit(1)

    return LocalLLMClient(
        model_name=args.model,
        base_url=args.url,
        sys_prompt_path=args.sys_prompt,
        max_iterations=args.max_iterations,
        disable_thinking=args.disable_thinking,
        session_file=session_file_to_load,
        options=config["model"]["options"],
        tools_config=config["tools"],
        history_dir=config["paths"]["history_dir"]
    )

def load_config_from_args() -> dict:
    """Lit uniquement --config pour charger le fichier avant de construire le vrai parser."""
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("-c", "--config", default=None)
    pre_args, _ = pre_parser.parse_known_args()

    if pre_args.config:
        return load_config(pre_args.config, explicit=True)
    return load_config(DEFAULT_CONFIG_PATH)

def main():
    config = load_config_from_args()
    args = build_parser(config).parse_args()
    history_dir = config["paths"]["history_dir"]

    if args.clear:
        SessionManager.clear(args.clear, history_dir)
        sys.exit(0)

    if args.list:
        SessionManager.list(history_dir)
        sys.exit(0)

    client = create_client(args, config)

    run_chat(client, history_dir)

if __name__ == "__main__":
    main()