from pathlib import Path
import json
from src.utils.find_session_file import find_session_file

class SessionManager:
    @staticmethod
    def list():
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