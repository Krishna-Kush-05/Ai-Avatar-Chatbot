# tts.py
import os
from elevenlabs.client import ElevenLabs

api_key = "set_api"

# Initialize ElevenLabs client
client = ElevenLabs(api_key=api_key)

def generate_audio(text, output_path="static/audio/output.mp3"):
    try:
        audio = client.text_to_speech.convert(
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # George
            text=text,
            model_id="eleven_monolingual_v1"
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        return output_path
    except Exception as e:
        print("TTS Error:", e)
        return None
