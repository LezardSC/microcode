import requests
import re

class TitleGenerator:
    def __init__(self, model, url):
        self.model = model
        self.url = url

    def generate(self, first_prompt: str) -> str:
        """Generate a title, stored in the session metadata."""
        payload = {
            "model": self.model,
            "messages": [{
                    "role": "system",
                    "content": "Generate a very short title (2 to 6 words) that sums up this prompt. Return ONLY the title."
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
