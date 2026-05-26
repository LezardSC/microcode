import requests
import json
from pathlib import Path

from tools import Tools

DEFAULT_SYS_PROMPT = "Tu es un assistant intelligent et utile. Réponds de manière concise et précise. Si tu ne connais pas la réponse, dis que tu ne sais pas plutôt que d'inventer une réponse."

class LocalLLMClient:
    """Handle communication with the locale API of the LLM."""
    def __init__(self, model_name="qwen3.5:9b", base_url="http://localhost:11434/api/chat", sys_prompt_path='system_prompt.txt'):
        self.model = model_name
        self.url = base_url

        system_prompt = self._read_system_prompt(sys_prompt_path)
        if not system_prompt:
            print(f"Error: Can't load '{sys_prompt_path}'. Using default system prompt.")
            system_prompt = DEFAULT_SYS_PROMPT

        self.messages = [{
            "role": "system",
            "content": system_prompt
        }]
        self.tools_instance = Tools()
        self.tools_schema = Tools.generate_schema()
    
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

    def send_message(self, user_content: str) -> str:
        self.messages.append({"role": "user", "content": user_content})

        request_payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": False,
            "tools": self.tools_schema
        }

        response = requests.post(self.url, json=request_payload)
        response.raise_for_status()
        message = response.json().get("message", {})

        if "tool_calls" in message:
            self.messages.append({
                "role": "assistant",
                "content": message.get("content", ""),
                "tool_calls": message["tool_calls"]
            })

            for tool_call in message["tool_calls"]:
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

            request_payload["messages"] = self.messages
            request_payload.pop("tools", None)

            final_response = requests.post(self.url, json=request_payload)
            final_response.raise_for_status()
            final_message = final_response.json().get("message", {})

            self.messages.append(final_message)

            return final_message.get("content", "")

        else:
            self.messages.append(message)
            return message.get("content", "")

