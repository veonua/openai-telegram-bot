from typing import Dict, Set
from collections import defaultdict

def is_markdown(text: str):
    return text.startswith("*") and text.endswith("*")


def entities_extract(message_text:str, entities) -> Dict[str, Set[str]]:
    d = defaultdict(set)
    for entity in entities:
        d[entity["type"]].add(message_text[entity["offset"] :entity["offset"] + entity["length"]])
    return d

class ReaderResult:
    def __init__(self, kind: str, text_content: str, title: str, byline: str, length: int, excerpt: str, site_name: str, language: str):
        self.kind = kind
        self.text_content = text_content.strip()
        self.title = title
        self.byline = byline
        self.length = length
        self.excerpt = excerpt
        self.site_name = site_name
        self.language = language

def fetch_url(url:str)->ReaderResult:
    import requests

    payload = 'url='+url
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }

    response = requests.request("POST", "https://reader-mauve-three.vercel.app/api/extract", headers=headers, data=payload)
    if response.status_code != 200:
        raise Exception("Error fetching url: "+str(response.status_code))
    
    data = response.json()
    return ReaderResult(data['kind'], data['textContent'], data['title'], data['byline'], data['length'], data['excerpt'], data['siteName'], data['language'])
    
