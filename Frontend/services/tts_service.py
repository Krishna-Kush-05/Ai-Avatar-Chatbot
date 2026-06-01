import os
import time
import uuid
import requests

# We import generate_audio from the top-level tts module
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tts import generate_audio

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

def generate_tts_audio(text: str) -> str:
    """
    TTS endpoint: ElevenLabs (primary) → gTTS (fallback).
    Generates a unique audio file per user to prevent caching/repeats,
    and cleans up old audio files to save space.
    Returns the generated audio filename (e.g., '1234.mp3') or None if failed.
    """
    audio_dir = os.path.join("static", "audio")
    os.makedirs(audio_dir, exist_ok=True)

    # Clean up old audio files (older than 120 seconds to allow chunk sequences)
    current_time = time.time()
    for file in os.listdir(audio_dir):
        if file.endswith(".mp3"):
            file_path = os.path.join(audio_dir, file)
            try:
                # remove if older than 120 seconds
                if current_time - os.path.getmtime(file_path) > 120:
                    os.remove(file_path)
            except Exception:
                pass

    # Create new unique file using UUID
    audio_filename = f"{uuid.uuid4().hex}.mp3"
    audio_path = os.path.join(audio_dir, audio_filename)

    # --- Primary: ElevenLabs high-quality TTS ---
    if ELEVENLABS_API_KEY:
        try:
            eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }
            resp = requests.post(eleven_url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                with open(audio_path, "wb") as f:
                    f.write(resp.content)
                return audio_filename
            else:
                print(f"ElevenLabs returned {resp.status_code}, falling back to gTTS")
        except Exception as e:
            print(f"ElevenLabs TTS failed ({e}), falling back to gTTS")

    # --- Fallback: gTTS ---
    result = generate_audio(text, audio_path)
    if result:
        return audio_filename

    return None
