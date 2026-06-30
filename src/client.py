import requests
import re
import json
from pathlib import Path
from typing import Iterator
from datetime import datetime

from session_manager import SessionManager
from title_generator import TitleGenerator
from tools import Tools

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

        self.tools_instance = Tools()
        self.tools_schema = Tools.generate_schema()
        self.title_generator = TitleGenerator(self.model, self.url)

        session_dir = Path("./historique")
        session_dir.mkdir(exist_ok=True)

        if session_file:
            session_path = session_dir / session_file
        else:
            created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            session_path = session_dir / f"{created_at}.json"
        
        self.session = SessionManager(session_path, self.model)

        if session_file:
            self.session.load()
        else:
            self._init_system_prompt(sys_prompt_path)
    
    @property
    def messages(self):
        """Permet un appel moins verbeux aux messages"""
        return self.session.messages
    
    @property
    def metadata(self):
        """Raccourci pour accéder aux métadonnées de la session"""
        return self.session.metadata
    
    def _init_system_prompt(self, sys_prompt_path):
        """Génère le prompt système initial."""
        system_prompt = self._read_system_prompt(sys_prompt_path)
        if not system_prompt:
            system_prompt = DEFAULT_SYS_PROMPT

        self.session.metadata["system_prompt"] = system_prompt    
        self.session.messages = [{"role": "system", "content": system_prompt}]
        self.session.save()
    
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
        self.session.add_message("user", user_content)

        if len(self.messages) == 2 and self.metadata.get("title") == "Nouvelle conversation":
            try:
                title= self.title_generator.generate(user_content)
                self.session.metadata["title"] = title
                self.session.rename(title)
            except Exception as e:
                print(f"\n[Warning: Impossible de générer le titre -> {e}]")

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
                self.session.add_message(
                    "assistant",
                    accumulated_message.get("content", ""),
                )
                self.session.save()
                return

            self.session.add_message(
                "assistant",
                accumulated_message["content"],
                extra={"tool_calls": accumulated_message["tool_calls"]}
            )

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
                    
                    self.session.add_message("tool", str(result)) 
                else:
                    self.session.add_message("tool", f"Error: the tool {func_name} doesn't exist.")

        self.session.save()
        yield "\nError: Maximum iterations reached without final response."
        return
