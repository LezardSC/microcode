import argparse
import sys
import requests
from src.client import LocalLLMClient
from src.session_manager import SessionManager
from src.utils.find_session_file import find_session_file

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

def run_chat(client: LocalLLMClient):
    print("Tapez 'quit' ou 'exit' pour quitter.\n")

    while True:
        try:
            content = input("Vous: ")

            if content.lower() in ["quit", "exit"]:
                print("\nEnd of conversation.")
                break

            if not content.strip():
                continue

            assistant_reply = client.send_message(content)

            print(f"\n\nAssistant:\n")
            for text_fragment in assistant_reply:
                print(text_fragment, end="", flush=True)
            print()

        except requests.exceptions.RequestException as e:
            print(f"\nNetwork Error: Can't join the API: {e}")
        except  KeyboardInterrupt:
            print("\nEnd of conversation.")
            return

def create_client(args) -> LocalLLMClient:
    session_file_to_load = None
    if args.resume:
        session_file_to_load = find_session_file(args.resume)
        if not session_file_to_load:
            print(f"Impossible de trouver une session correspondant à '{args.resume}'")
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