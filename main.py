import requests
import argparse
from client import LocalLLMClient

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

    return parser


def main():
    args = build_parser().parse_args()
    client = LocalLLMClient(
        model_name=args.model,
        base_url=args.url,
        sys_prompt_path=args.sys_prompt,
        max_iterations=args.max_iterations,
        disable_thinking=args.disable_thinking,
    )

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
            break

if __name__ == "__main__":
    main()
