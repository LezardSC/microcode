from pathlib import Path
import re
import json
from datetime import datetime
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.table import Table

from utils.find_session_file import find_session_file

console = Console()

class SessionManager:
    def __init__(self, session_path: Path, model: str = "qwen3.5:9b"):
        self.session_path = Path(session_path)
        self.model = model
        self.metadata = {
            "model": self.model,
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "system_prompt": "",
            "title": "New conversation"
        }
        self.messages = []
    
    def load(self):
        """Load an existing session, metadata and messages."""
        if self.session_path.exists():
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                self.metadata = data.get("metadata", self.metadata)
                self.messages = data.get("messages", [])

                console.print(f"[bold cyan]Session loaded: {self.metadata.get('title', 'Untitled')} ({self.session_path.name})[/bold cyan]")

    def save(self):
        """Save the session (metadata + messages)."""
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
    def list(sessions_dir: str = "history"):
        """Print every session available in the history folder."""

        sessions_dir = Path(sessions_dir)
        if not sessions_dir.exists():
            console.print("[yellow]Error: Folder not found.[/yellow]")
            return
        
        files = sorted(list(sessions_dir.glob("*.json")))
        if not files:
            console.print("[yellow]No session found. Start a conversation to have it saved![/yellow]")
            return
        
        table = Table(title="Conversation history", title_style="bold blue")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("File", style="magenta")
        table.add_column("Model", style="green")
        table.add_column("Title", style="white")

        for idx, f in enumerate(files, start=1):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    meta = data.get("metadata", {})
                    title = meta.get("title", "Untitled")
                    model = meta.get("model", "unknown")

                    display_title = (title[:40] + '..') if len(title) > 40 else title
                    table.add_row(str(idx), f.name, model, display_title)
            except Exception:
                table.add_row(str(idx), f.name, "---", "[red]/!\\ Corrupted file[/red]")
        console.print(table)
        print()
    
    @staticmethod
    def clear(target: str, sessions_dir: str = "history"):
        """Delete sessions."""
        sessions_dir = Path(sessions_dir)
        if not sessions_dir.exists():
            console.print("[yellow]No history folder to clean.[/yellow]")
            return
        
        if target.lower() == "all":
            files = list(sessions_dir.glob("*.json"))
            if not files:
                console.print("[yellow]The history is already empty.[/yellow]")
                return
            
            prompt_session = PromptSession()
            confirm = prompt_session.prompt(f"Are you sure you want to delete every session ({len(files)} files)? [y/N]:\n")
            if confirm.lower() == 'y':
                for f in files:
                    f.unlink()
                console.print("[bold green]All sessions were deleted.[/bold green]")
            else:
                console.print("Deletion cancelled.")
            return
        
        file_to_delete = find_session_file(target, sessions_dir)

        if file_to_delete:
            target_path = sessions_dir / file_to_delete
            target_path.unlink()
            console.print(f"[bold green]Session '{file_to_delete}' deleted.[/bold green]")
        else:
            console.print(f"[bold red]No session matches '{target}'.[/bold red]")
    
    def rename(self, title: str):
        safe_filename = re.sub(r'[^\w\s-]', '', title).strip().lower()
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename)

        if not safe_filename:
            safe_filename = "untitled_conversation"
        
        new_path = self.session_path.parent / f"{safe_filename}.json"

        counter = 1
        while new_path.exists():
            new_path = self.session_path.parent / f"{safe_filename}_{counter}.json"
            counter += 1
        
        if self.session_path.exists():
            self.session_path.rename(new_path)
        
        self.session_path = new_path