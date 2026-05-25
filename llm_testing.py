import requests
import inspect
import ast
import operator
import json
import os
from pathlib import Path
from datetime import datetime

class Tools:
    def _evaluate_ast(self, node):
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) in allowed_operators:
                return allowed_operators[type(node.op)](self._evaluate_ast(node.operand))
        
        elif isinstance(node, ast.BinOp):
            if type(node.op) in allowed_operators:
                left = self._evaluate_ast(node.left)
                right = self._evaluate_ast(node.right)

                if isinstance(node.op, ast.Pow) and right > 1000:
                    raise ValueError("exponant too large.")
                
                return allowed_operators[type(node.op)](left, right)
        
        raise ValueError(f"Unauthorized element: {type(node).__name__}")


    def calculate(self, expression: str) -> str:
        """
        Evaluate a simple mathematical expression.
        expression: The operation to calculate (example: '2 + 2', '10 / 3 + 1').
        """
        try:
            tree = ast.parse(expression, mode='eval').body
            resultat = self._evaluate_ast(tree)
            
            return str(resultat)
        
        except SyntaxError:
            return "Error: Invalid mathematic syntax."
        except ZeroDivisionError:
            return "Error: Can't divide by 0."
        except Exception as e:
            return f"Error: {e}"
    
    def read_file(self, path: str) -> str:
        """
        Lit le contenu textuel d'un fichier local (code, txt, md, csv, etc.) pour l'analyser.
        Prend en charge les chemins relatifs ou absolus.
        path: Le chemin vers le fichier (example. 'data.txt', '/home/user/script.py' ou 'C:\\Users\\...').
        """
        try:
            clean_path = path.strip("'\"")

            # If the path start with a letter of Window disk (ex: C:\ ou D:\) and we're on WSL/Linux
            if os.name == 'posix' and len(clean_path) > 1 and clean_path[1] == ':':
                drive = clean_path[0].lower()
                remainder = clean_path[2:].replace('\\', '/')
                clean_path = f"/mnt/{drive}{remainder}"
            
            file_path = Path(clean_path)

            if not file_path.exists():
                return f"Error: The file at path '{path}' doesn't exist."
            if not file_path.is_file():
                return f"Error: '{path} is a folder, not a readable file."

            # Reading the file with size limitation (1000 kb so 1Mb)
            max_bytes = 1000 * 1024
            if file_path.stat().st_size > max_bytes:
                return f"Error: The file is too big ({file_path().st_size / 1024:.1f}). The limit is 1Mb."
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return f"content of file '{file_path.name}': \n{content}"
        
        except Exception as e:
            return f"Error: Can't read the file: {e}"


    def get_weather(self, city: str) -> str:
        """
        Obtient les conditions météo actuelles pour une ville donnée.
        city: Le nom de la ville ou de la région (example: )
        """
        try:
            # wttr.in?format=3 return a single clean line: "Paris: ⛅️ +18°C ↙️ 11km/h"
            # format=4 give even more details (wetness, rain...)
            url = f"https://wttr.in/{city}?format=4&lang=fr"
            headers = {
                "User-Agent": "local_llm_client/1.0"
            }

            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            if "Location not found" in response.text or "wttr.in" in response.text.lower():
                return f"meteo not found for the city: '{city}'."
            
            return f"Meteo in {city}:\n{response.text.strip()}"

        except Exception as e:
            return f"Can't get meteo for {city}. Error: {e}."

    def search_wikipedia(self, query: str) -> str:
        """
        À utiliser si l'utilisateur demande une information 
        historique, une biographie, un fait précis ou un concept technique que tu ne connais pas.
        NE PAS utiliser pour les discussions générales, les salutations, ou si tu possèdes 
        déjà la réponse de manière certaine dans tes connaissances.
        query: Le sujet précis à rechercher, en français (même si l'utilisateur écrit 
        dans une autre langue, il faudra retraduire derrière).
        """
        try:
            api = "https://fr.wikipedia.org/w/api.php"
            headers = {
                "User-Agent": "local_llm_client/1.0"
            }

            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json"
            }

            search_response = requests.get(api, params=search_params, headers=headers)
            search_response.raise_for_status()
            search_data = search_response.json()

            results = search_data.get("query", {}).get("search", [])

            if not results:
                return f"No result found on Wikipedia for the research: '{query}'."
            
            best_title = results[0]["title"]

            params = {
                "action": "query",
                "titles": best_title,
                "explaintext": True,
                "prop": "extracts",
                "exlimit": 1,
                "format": "json",
                "redirects": 1
            }

            response = requests.get(api, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            page_id = next(iter(pages))
            page_data = pages[page_id]

            if page_id == "-1" or "extract" not in page_data:
                return f"The Wikipedia page found for '{best_title}' is empty or can't be found."
            
            extract = page_data["extract"]

            return f"Informations found on Wikipedia for '{best_title}':\n{extract}"
        
        except Exception as e:
            return f"Error on Wikipedia search: {str(e)}."


    def get_time(self):
        """
        Get the date and time of the system.
        """
        return str(datetime.now())

    @classmethod
    def generate_schema(cls) -> list:
        """"Generate dynamically the 'tools' config for the API."""

        schema = []
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_') and name != 'generate_schema':
                description = inspect.getdoc(method) or "No description given."

                sig = inspect.signature(method)
                properties = {}
                required_params = []

                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue

                    param_type = "string"
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"

                    properties[param_name] = {
                        "type": param_type,
                        "description": f"Parameter {param_name}"
                    }

                    if param.default == inspect.Parameter.empty:
                        required_params.append(param_name)

                schema.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": required_params,
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
            print(f"\nNetwork Error: Can't join the API: {e}")
        except  KeyboardInterrupt:
            print("\nEnd of conversation.")
            break

if __name__ == "__main__":
    main()
