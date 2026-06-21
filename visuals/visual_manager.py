import os
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_topic(query: str) -> str:
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract the single main educational topic (1-3 words in English) "
                    "from the teacher's instruction. Reply with ONLY the topic name, nothing else."
                )
            },
            {"role": "user", "content": query}
        ],
        max_tokens=15
    )
    return resp.choices[0].message.content.strip()

def get_visual(query: str):
    try:
        topic = extract_topic(query)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}"
        resp = requests.get(url, timeout=5, headers={"User-Agent": "TeachingAssistant/1.0"})
        if resp.ok:
            data = resp.json()
            return {
                "topic":       topic,
                "title":       data.get("title", topic),
                "image_url":   data.get("thumbnail", {}).get("source"),
                "description": data.get("extract", "")[:350]
            }
    except Exception:
        pass
    return None
