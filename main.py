import argparse

import sys
import json
from pathlib import Path

import requests
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

def list_sessions():
    """Affiche toutes tles sessions disponibles dans ./historique/"""
    sessions_dir = Path("./historique")
    if not sessions_dir.exists():
        print("Erreur: Dossier introuvable.")
        return
    
    files = sorted(list(sessions_dir.glob("*.json")))
    if not files:
        print("Aucune session trouvée. Commence une conversation pour qu'elle soit sauvegardée.")
        return
    
    print(f"\n{'ID':<3} | {'Fichier':<25} | {'Modèle':<15} | {'Titre'}")
    print("-" * 75)

    for idx, f in enumerate(files, start=1):
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                meta = data.get("metadata", {})
                title = meta.get("title", "Sans titre")
                model = meta.get("model", "inconnu")

                display_title = (title[:40] + '..') if len(title) > 40 else title
                print(f"{idx:<3} | {f.name:<25} | {model:<15} | {display_title}")
        except Exception:
            print(f"{f.name:<25} | /!\\ Fichier Corrompu")
    print()

def find_session_file(target: str) -> str:
    """Trouve le fichier correspondant (dernier modifié, ou par nom)."""
    sessions_dir = Path("./historique")
    if not sessions_dir.exists():
        return None

    files = sorted(list(sessions_dir.glob("*.json")))
    if not files:
        return None

    if target == "LAST":
        latest_file = max(files, key=lambda p: p.stat().st_mtime)
        return latest_file.name
    
    if target.isdigit():
        idx = int(target)
        if 1 <= idx <= len(files):
            return files[idx - 1].name
        else:
            return None
    
    for f in files:
        if target in f.name:
            return f.name

    return None

def clear_session(target: str):
    """Gère la suppression des sessions."""
    sessions_dir = Path("./historique")
    if not sessions_dir.exists():
        print("Aucun dossier d'historique à nettoyer")
        return
    
    if target.lower() == "all":
        files = list(sessions_dir.glob("*.json"))
        if not files:
            print("L'historique est déjà vide.")
            return
        
        confirm = input(f"Êtes-vous sûr de vouloir supprimer toutes les sessions ({len(files)} fichiers) ? [Y/n]:\n")
        if confirm.lower() == 'y':
            for f in files:
                f.unlink()
            print("Toutes les sessions ont été supprimées.")
        else:
            print("Suppression annulée.")
        return
    
    file_to_delete = find_session_file(target)

    if file_to_delete:
        target_path = sessions_dir / file_to_delete
        target_path.unlink()
        print(f"Session ' {file_to_delete}' supprimée avec succès.")
    else:
        print(f"Impossible de trouver la session correspondant à '{target}'.")

def main():
    args = build_parser().parse_args()

    if args.clear:
        clear_session(args.clear)
        sys.exit(0)

    if args.list:
        list_sessions()
        sys.exit(0)

    session_file_to_load = None
    if args.resume:
        session_file_to_load = find_session_file(args.resume)
        if not session_file_to_load:
            print(f"Impossible de trouver une session correspondant à '{args.resume}'")
            sys.exit(1)

    client = LocalLLMClient(
        model_name=args.model,
        base_url=args.url,
        sys_prompt_path=args.sys_prompt,
        max_iterations=args.max_iterations,
        disable_thinking=args.disable_thinking,
        session_file=session_file_to_load
    )

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
            break

if __name__ == "__main__":
    main()
