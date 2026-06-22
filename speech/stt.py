from groq import Groq
import os


from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Known Whisper hallucination phrases to reject
HALLUCINATIONS = {
    "झाल", "झाल झाल", "धन्यवाद", "subscribe", "subscribed",
    "thank you", "thanks for watching", ".", "..", "...", ""
}

def speech_to_text(audio_path):
    print("Audio path:", audio_path)
    print("File exists:", os.path.exists(audio_path))
    # Reject tiny/empty audio files (< 5KB = likely silence
    file_size = os.path.getsize(audio_path)
    if file_size < 5000:
        return "[Audio too short — please speak clearly and try again]"

    _, ext = os.path.splitext(audio_path)
    ext = ext.lower().strip(".")
    mime_type = "audio/mpeg" if ext == "mp3" else f"audio/{ext}" if ext else "audio/webm"

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=(os.path.basename(audio_path), audio_file, mime_type),
            prompt="Teacher is giving instructions to students in Hindi or Hinglish.",
            response_format="text"
        )

    result = transcription.strip()

    # Reject known hallucinated phrases
    if result.lower().strip(".,!? ") in {h.lower() for h in HALLUCINATIONS}:
        return "[Could not understand — please speak again]"

    return result
