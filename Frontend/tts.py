# tts.py
# ─────────────────────────────────────────────────────────────
# Dual TTS system
#   Primary  → ElevenLabs  (high quality, needs ELEVENLABS_API_KEY)
#                           Handled inline in app.py /speak route.
#   Fallback → gTTS         (free, no API key needed)
#                           This module implements the gTTS fallback.
# ─────────────────────────────────────────────────────────────
import os
import uuid
from gtts import gTTS


def generate_audio(text: str, output_path: str = None):
    if output_path is None:
        output_path = f"static/audio/{uuid.uuid4().hex}.mp3"
    """
    Generate speech audio using gTTS (Google Text-to-Speech).

    Called by the Flask /speak route when ElevenLabs is unavailable
    or returns an error.  Cache-busting is handled by the caller.

    Returns output_path on success, None on failure.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"[gTTS fallback] Error: {e}")
        return None
