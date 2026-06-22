import edge_tts
import asyncio
import threading
import os
import uuid

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
    os.makedirs("temp", exist_ok=True)
    # Unique filename per call — avoids race conditions when TTS is called
    # multiple times (e.g. quiz question audio + feedback audio in one session)
    output_path = f"temp/tts_{uuid.uuid4().hex[:8]}.mp3"

    def run():
        asyncio.run(_generate(text, voice, output_path))

    t = threading.Thread(target=run)
    t.start()
    t.join()
    return output_path