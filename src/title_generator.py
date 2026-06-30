import requests
import re

class TitleGenerator:
    def __init__(self, model, url):
        self.model = model
        self.url = url

    def generate(self, first_prompt: str) -> str:
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

        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        raw_title = response.json()["message"]["content"].strip()
        clean_title = re.sub(r'[\n\r"]+', '', raw_title)
        return clean_title
