import requests
import json
import re
from pathlib import Path
from typing import Iterator
from datetime import datetime

from src.tools import Tools

DEFAULT_SYS_PROMPT = "Tu es un assistant intelligent et utile. Réponds de manière concise et précise. Si tu ne connais pas la réponse, dis que tu ne sais pas plutôt que d'inventer une réponse."

class LocalLLMClient:
    """Handle communication with the locale API of the LLM."""
    def __init__(
            self,
            model_name="qwen3.5:9b",
            base_url="http://localhost:11434/api/chat",
            sys_prompt_path='system_prompt.txt',
            max_iterations=15,
            disable_thinking=False,
            session_file=None):
        self.model = model_name
        self.url = base_url
        self.max_iterations = max_iterations
        self.disable_thinking = disable_thinking

        self.messages = []
        self.tools_instance = Tools()
        self.tools_schema = Tools.generate_schema()

        self.metadata = {
            "model": self.model,
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "system_prompt": "",
            "title": "Nouvelle conversation"
        }

        self.session_dir = Path("./historique")
        self.session_dir.mkdir(exist_ok=True)

        if session_file:
            self.session_path = self.session_dir / session_file
            self._load_session(sys_prompt_path)
        else:
            filename = f"{self.metadata['created_at']}.json"
            self.session_path = self.session_dir / filename
            self._init_system_prompt(sys_prompt_path)

    def _load_session(self, sys_prompt_path):
        """Charge une session existante incluant métadonnées et messages."""
        if self.session_path.exists():
            try:
                with open(self.session_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.metadata = data.get("metadata", self.metadata)
                    self.messages = data.get("messages", [])
                    print(f"Session chargée: {self.metadata.get('title', 'Sans titre')} ({self.session_path.name})")
            except Exception as e:
                print(f"Erreur lors du chargement de la session: {e}")
                self._init_system_prompt(sys_prompt_path)
    
    def _init_system_prompt(self, sys_prompt_path):
        """Génère le prompt système initial."""
        system_prompt = self._read_system_prompt(sys_prompt_path)
        if not system_prompt:
            system_prompt = DEFAULT_SYS_PROMPT

        self.metadata["system_prompt"] = system_prompt    
        self.messages = [{"role": "system", "content": system_prompt}]
        self._save_session()
    
    def _save_session(self):
        """Sauvegarde la session (métadonnées + messages)."""
        self.metadata["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        data = {
            "metadata": self.metadata,
            "messages": self.messages
        }
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_title(self, first_prompt: str):
        """Génère un titre stocké dans les métadonnées"""
        payload = {
            "model": self.model,
            "messages": [{
                    "role": "system",
                    "content": "Génère un titre ultra court (2 à 6 mots) qui résume ce prompt. Ne renvoie QUE le titre."
                },
                {"role": "user", "content": first_prompt}
            ],
            "think": False,
            "stream": False,
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            raw_title = response.json()["message"]["content"].strip()
            clean_title = re.sub(r'[\n\r"]+', '', raw_title)
            self.metadata["title"] = clean_title

            safe_filename = re.sub(r'[^\w\s-]', '', clean_title).strip().lower()
            safe_filename = re.sub(r'[-\s]+', '_', safe_filename)

            if not safe_filename:
                safe_filename = "conversation_sans_titre"
            
            new_path = self.session_dir / f"{safe_filename}.json"

            counter = 1
            while new_path.exists():
                new_path = self.session_dir / f"{safe_filename}_{counter}.json"
                counter += 1
            
            if self.session_path.exists():
                self.session_path.rename(new_path)
            
            self.session_path = new_path

        except Exception as e:
            print(f"\n[Warning: Impossible de générer le titre -> {e}]")
            self.metadata["title"] = "Conversation sans titre"
    
    def _read_system_prompt(self, path: str) -> str:
        max_bytes = 50_000
        p = Path(path)

        try:
            target = p.resolve(strict=False)
        except Exception as e:
            print(f"Error: Invalid system prompt path '{path}': {e}.")
            return ""
        
        try:
            with open(target, "rb") as f:
                data = f.read(max_bytes + 1)
        except FileNotFoundError:
            print(f"Error: System prompt file '{path}' not found.")
            return ""
        except (PermissionError, IsADirectoryError, OSError) as e:
            print(f"Error: Cannot read system prompt from '{path}': {e}.")
            return ""

        if len(data) > max_bytes:
            print(f"Error: System prompt file '{path}' exceeds the maximum size of {max_bytes} bytes.")
            return ""
        
        try:
            return data.decode(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Error: Cannot decode system prompt from '{path}': {e}.")
            return ""

    def send_message(self, user_content: str) -> Iterator[str]:
        self.messages.append({"role": "user", "content": user_content})

        if len(self.messages) == 2 and self.metadata.get("title") == "Nouvelle conversation":
            self._generate_title(user_content)
        
        for _ in range(self.max_iterations):
            request_payload = {
                "model": self.model,
                "messages": self.messages,
                "stream": True,
                "tools": self.tools_schema,
            }
            if self.disable_thinking:
                request_payload["think"] = False

            response = requests.post(self.url, json=request_payload)
            response.raise_for_status()

            accumulated_message = {
                "role": "assistant",
                "content": "",
            }

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        msg_chunk = chunk["message"]

                        content_piece = msg_chunk.get("content", "")
                        if content_piece:
                            accumulated_message["content"] += content_piece
                            yield content_piece  # Stream the content piece to the caller
                        
                        if "tool_calls" in msg_chunk:
                            accumulated_message["tool_calls"] = msg_chunk["tool_calls"]
            
            if "tool_calls" not in accumulated_message and accumulated_message["content"].strip():
                self.messages.append(accumulated_message)
                self._save_session()
                return

            self.messages.append(accumulated_message)

            for tool_call in accumulated_message["tool_calls"]:
                func_name = tool_call["function"]["name"]

                if hasattr(self.tools_instance, func_name):
                    func = getattr(self.tools_instance, func_name)

                    arguments = tool_call["function"].get("arguments", {})
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {}
                    
                    try:
                        result = func(**arguments)
                    except Exception as e:
                        result = f"Execution error for {func_name}: {e}"
                    
                    self.messages.append({
                        "role": "tool",
                        "content": str(result),
                    })
                else:
                    self.messages.append({
                        "role": "tool",
                        "content": f"Error: the tool {func_name} doesn't exit.",
                    })

        self._save_session()
        yield "\nError: Maximum iterations reached without final response."
        return
