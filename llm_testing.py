import requests
import inspect
from datetime import datetime

class Tools:
    def get_time(self):
        return str(datetime.now())

    @classmethod
    def generate_schema(cls) -> list:
        """"Generate dynamically the 'tools' config for the API."""

        schema = []
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_') and name != 'generate_schema':
                description = inspect.getdoc(method) or "No description given."
                schema.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                })

        return schema


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
                    result = func()

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


def main():
    print("Bienvenue dans l'instance de Qwen3.5:9b\n")
    client = LocalLLMClient()

    while True:
        try:
            content = input("Vous: ")

            if content.lower() in ["quit", "exit"]:
                print("\nEnd of conversation.")
                break

            if not content.strip():
                continue

            assistant_reply = client.send_message(content)
            print(f"\nAssistant:\n{assistant_reply}\n")

        except requests.exceptions.RequestException as e:
            print("f\nNetwork Error: Can't join the API: {e}")
        except  KeyboardInterrupt:
            print("\nEnd of conversation.")
            break

if __name__ == "__main__":
    main()
