import os
import inspect
import requests
from pathlib import Path
from datetime import datetime
import ast

from ddgs import DDGS
from bs4 import BeautifulSoup

from src.utils.math_eval import evaluate_ast

class Tools:
    def fetch_url(self, url: str) -> str:
        """
        Lit et extrait le contenu textuel complet d'une page Web spécifique.
        Peut être utilisé après l'outil `search_web` en lui passant l'URL exacte à explorer.
        url: L'adresse complète de la page (ex: 'https://google.com') 
        """
        try:
            # Using a common User-Agent to avoid being blocked by some websites.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            page = requests.get(url, headers=headers, timeout=8)
            page.raise_for_status()

            soup = BeautifulSoup(page.content, 'html.parser')

            # Cleaning the page
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                element.extract()

            text = soup.get_text(separator=' ', strip=True)

            extract = text[:5000]
            if len(text) > 5000:
                extract += "\n\n[The content is too long, only the first 5000 characters are shown.]"

            return f"Content of the page at URL '{url}':\n{extract}"

        except requests.exceptions.Timeout:
            return f"Error: The request to '{url}' timed out."
        except Exception as e:
            return f"Error fetching URL: {e}"

    def search_web(self, query: str) -> str:
        """
        Recherche des informations récentes ou des actualités sur Internet.
        A utiliser uniquement si tes connaissances ne suffisent pas.
        Utilise cet outil pour découvrir des URL pertinentes que tu pourras ensuite explorer avec `fetch_url` si besoin.
        query: les mots-clés de la recherche.
        """
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=10)]

            if not results:
                return f"No result found on Internet for '{query}'."
            
            context = f"Results for Internet search of '{query}': \n\n"
            for i, res in enumerate(results, 1):
                title = res.get('title', 'unknown title')
                context += f"[{i}] Title: {title}\nURL: {res['href']}\nExtract: {res['body'][:1000]}\n\n"
        
            return context

        except Exception as e:
            return f"Error on Internet search: {e}"

    def calculate(self, expression: str) -> str:
        """
        Evaluate a simple mathematical expression.
        expression: The operation to calculate (example: '2 + 2', '10 / 3 + 1').
        """
        try:
            # split an expression into a tree of mathematical objects
            tree = ast.parse(expression, mode='eval').body
            resultat = evaluate_ast(tree)
            
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

            # Reading the file with size limitation (500 kb)
            max_bytes = 500 * 1024
            if file_path.stat().st_size > max_bytes:
                return f"Error: The file is too big ({file_path().stat().st_size / 1024:.1f}). The limit is 1Mb."
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return f"content of file '{file_path.name}': \n{content}"
        
        except Exception as e:
            return f"Error: Can't read the file: {e}"


    def get_weather(self, city: str) -> str:
        """
        Obtient les conditions météo actuelles pour une ville donnée.
        city: Le nom de la ville ou de la région (example: 'Paris', 'Texas')
        """
        try:
            # wttr.in?format=3 return a single clean line: "Paris: ⛅️ +18°C ↙️ 11km/h"
            # format=4 give even more details (wetness, rain...)
            url = f"https://wttr.in/{city}?format=4&lang=fr"
            headers = {
                "User-Agent": "local_llm_client/1.0"
            }

            page = requests.get(url, headers=headers, timeout=8)
            page.raise_for_status()


            if "Location not found" in page.text:
                return f"meteo not found for the city: '{city}'."
            
            return f"Meteo in {city}:\n{page.text.strip()}"

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
                "exintro": True,
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

        # get all functions in Tools class
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_') and name != 'generate_schema':
                # read the docstring and change it into a description of the tool.
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
                            "properties": properties,
                            "required": required_params,
                        }
                    }
                })

        return schema

