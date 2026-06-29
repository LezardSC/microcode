from pathlib import Path

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

