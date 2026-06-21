import edge_tts
import asyncio
import threading
import os

VOICE_MAP = {
    "Hindi":    "hi-IN-SwaraNeural",
    "English":  "en-IN-NeerjaNeural",
    "Hinglish": "hi-IN-SwaraNeural"
}

async def _generate(text, voice, path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)

def text_to_speech(text, language="Hinglish"):
    voice = VOICE_MAP.get(language, "hi-IN-SwaraNeural")
    output_path = "temp/output.mp3"
    os.makedirs("temp", exist_ok=True)

    def run():
        asyncio.run(_generate(text, voice, output_path))

    t = threading.Thread(target=run)
    t.start()
    t.join()
    return output_path