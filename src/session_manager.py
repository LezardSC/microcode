from pathlib import Path
import json
from datetime import datetime
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.table import Table

from utils.find_session_file import find_session_file

class SessionManager:
    def __init__(self, session_path: Path, model: str = "qwen3.5:9b"):
        self.session_path = Path(session_path)
        self.model = model
        self.metadata = {
            "model": self.model,
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "system_prompt": "",
            "title": "Nouvelle conversation"
        }
        self.messages = []
    
    def load(self):
        """Charge une session existante incluant métadonnées et messages."""
        if self.session_path.exists():
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                self.metadata = data.get("metadata", self.metadata)
                self.messages = data.get("messages", [])

                print(f"Session chargée: {self.metadata.get('title', 'Sans titre')} ({self.session_path.name})")

    def append_message(self, message):
        self.messages.append(message)

    def save(self):
        """Sauvegarde la session (métadonnées + messages)."""
        self.metadata["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        data = {
            "metadata": self.metadata,
            "messages": self.messages
        }
        
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_message(self, role, content, extra=None):
        msg = {"role": role, "content": content}
        if extra:
            msg.update(extra)
        self.messages.append(msg)

    @staticmethod
    def list():
        """Affiche toutes les sessions disponibles dans ./historique/"""
        console = Console()

        sessions_dir = Path("./historique")
        if not sessions_dir.exists():
            print("[yellow]Erreur: Dossier introuvable.[/yellow]")
            return
        
        files = sorted(list(sessions_dir.glob("*.json")))
        if not files:
            print("[yellow]Aucune session trouvée. Commence une conversation pour qu'elle soit sauvegardée.![/yellow]")
            return
        
        table = Table(title="Historique des Conversations", title_style="bold blue")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Fichier", style="magenta")
        table.add_column("Modèle", style="green")
        table.add_column("Titre", style="white")

        for idx, f in enumerate(files, start=1):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    meta = data.get("metadata", {})
                    title = meta.get("title", "Sans titre")
                    model = meta.get("model", "inconnu")

                    display_title = (title[:40] + '..') if len(title) > 40 else title
                    table.add_row(str(idx), f.name, model, display_title)
            except Exception:
                table.add_row(str(idx), f.name, "---", "[red]/!\\ Fichier Corrompu[/red]")
        console.print(table)
        print()
    
    @staticmethod
    def clear(target: str):
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
            
            prompt_session = PromptSession()
            confirm = prompt_session.prompt(f"Êtes-vous sûr de vouloir supprimer toutes les sessions ({len(files)} fichiers) ? [Y/n]:\n")
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
    