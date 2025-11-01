# tts.py
import pyttsx3
import os

def generate_audio(text, output_path="static/audio/output.mp3"):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Initialize local TTS engine
        engine = pyttsx3.init()

        # Optional: adjust rate, volume, and voice
        engine.setProperty("rate", 180)    # speed of speech
        engine.setProperty("volume", 1.0)  # volume (0.0 to 1.0)

        # Choose a voice if available
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)  # pick first voice

        # Save speech to file
        engine.save_to_file(text, output_path)
        engine.runAndWait()

        print(f"TTS generated: {output_path}")
        return output_path

    except Exception as e:
        print("TTS Error:", e)
        return None