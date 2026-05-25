import requests
import json
from tools import Tools

class LocalLLMClient:
    """Handle communication with the locale API of the LLM."""
    def __init__(self, model_name="qwen3.5:9b", base_url="http://localhost:11434/api/chat"):
        self.model = model_name
        self.url = base_url
        self.messages = []
        self.tools_instance = Tools()
        self.tools_schema = Tools.generate_schema()
    
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

