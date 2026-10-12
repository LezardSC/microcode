import os
import inspect
import requests
from pathlib import Path
from datetime import datetime
import ast

from ddgs import DDGS
from bs4 import BeautifulSoup

from utils.math_eval import evaluate_ast

class Tools:
    def __init__(
            self,
            request_timeout=8,
            fetch_url_max_chars=5000,
            read_file_max_kb=500,
            search_max_results=10,
            search_extract_chars=1000):
        self._timeout = request_timeout
        self._fetch_url_max_chars = fetch_url_max_chars
        self._read_file_max_kb = read_file_max_kb
        self._search_max_results = search_max_results
        self._search_extract_chars = search_extract_chars

    def fetch_url(self, url: str) -> str:
        """
        Read and extract the full text content of a specific web page.
        Can be used after the `search_web` tool, by passing it the exact URL to explore.
        url: The full address of the page (e.g. 'https://google.com')
        """
        try:
            # Using a common User-Agent to avoid being blocked by some websites.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            page = requests.get(url, headers=headers, timeout=self._timeout)
            page.raise_for_status()

            soup = BeautifulSoup(page.content, 'html.parser')

            # Cleaning the page
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                element.extract()

            text = soup.get_text(separator=' ', strip=True)

            max_chars = self._fetch_url_max_chars
            extract = text[:max_chars]
            if len(text) > max_chars:
                extract += f"\n\n[The content is too long, only the first {max_chars} characters are shown.]"

            return f"Content of the page at URL '{url}':\n{extract}"

        except requests.exceptions.Timeout:
            return f"Error: The request to '{url}' timed out."
        except Exception as e:
            return f"Error fetching URL: {e}"

    def search_web(self, query: str) -> str:
        """
        Search the Internet for recent information or news.
        Use it only when your own knowledge isn't enough.
        Use this tool to find relevant URLs, which you can then explore with `fetch_url` if needed.
        query: the search keywords.
        """
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=self._search_max_results)]

            if not results:
                return f"No result found on Internet for '{query}'."
            
            context = f"Results for Internet search of '{query}': \n\n"
            for i, res in enumerate(results, 1):
                title = res.get('title', 'unknown title')
                context += f"[{i}] Title: {title}\nURL: {res['href']}\nExtract: {res['body'][:self._search_extract_chars]}\n\n"
        
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
            result = evaluate_ast(tree)
            
            return str(result)
        
        except SyntaxError:
            return "Error: Invalid mathematic syntax."
        except ZeroDivisionError:
            return "Error: Can't divide by 0."
        except Exception as e:
            return f"Error: {e}"

    
    def read_file(self, path: str) -> str:
        """
        Read the text content of a local file (code, txt, md, csv, etc.) to analyse it.
        Accepts relative or absolute paths.
        path: The path to the file (e.g. 'data.txt', '/home/user/script.py' or 'C:\\Users\\...').
        """
        try:
            clean_path = path.strip("'\"")

            # If the path starts with a Windows drive letter (e.g. C:\ or D:\) and we're on WSL/Linux
            if os.name == 'posix' and len(clean_path) > 1 and clean_path[1] == ':':
                drive = clean_path[0].lower()
                remainder = clean_path[2:].replace('\\', '/')
                clean_path = f"/mnt/{drive}{remainder}"
            
            file_path = Path(clean_path)

            if not file_path.exists():
                return f"Error: The file at path '{path}' doesn't exist."
            if not file_path.is_file():
                return f"Error: '{path} is a folder, not a readable file."

            # Reading the file with size limitation
            max_bytes = self._read_file_max_kb * 1024
            if file_path.stat().st_size > max_bytes:
                return f"Error: The file is too big ({file_path.stat().st_size / 1024:.1f} KB). The limit is {self._read_file_max_kb} KB."
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return f"content of file '{file_path.name}': \n{content}"
        
        except Exception as e:
            return f"Error: Can't read the file: {e}"


    def get_weather(self, city: str) -> str:
        """
        Get the current weather conditions for a given city.
        city: The name of the city or region (e.g. 'Paris', 'Texas')
        """
        try:
            # wttr.in?format=3 return a single clean line: "Paris: ⛅️ +18°C ↙️ 11km/h"
            # format=4 give even more details (wetness, rain...)
            url = f"https://wttr.in/{city}?format=4"
            headers = {
                "User-Agent": "local_llm_client/1.0"
            }

            page = requests.get(url, headers=headers, timeout=self._timeout)
            page.raise_for_status()


            if "Location not found" in page.text:
                return f"Weather not found for the city: '{city}'."
            
            return f"Weather in {city}:\n{page.text.strip()}"

        except Exception as e:
            return f"Error: Can't get the weather for {city}: {e}."

    def search_wikipedia(self, query: str) -> str:
        """
        Use it when the user asks for historical information, a biography,
        a precise fact or a technical concept you don't know.
        DO NOT use it for general discussion, greetings, or when you already
        know the answer for certain.
        query: The precise subject to search for, in English (even if the user writes
        in another language; translate the result back afterwards).
        """
        try:
            api = "https://en.wikipedia.org/w/api.php"
            headers = {
                "User-Agent": "local_llm_client/1.0"
            }

            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json"
            }

            search_response = requests.get(api, params=search_params, headers=headers, timeout=self._timeout)
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

            response = requests.get(api, params=params, headers=headers, timeout=self._timeout)
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

