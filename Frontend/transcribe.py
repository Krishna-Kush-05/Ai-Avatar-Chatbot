# transcribe.py — using FasterWhisper instead of ElevenLabs

import os
from werkzeug.utils import secure_filename
from faster_whisper import WhisperModel

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Model placeholder for singleton pattern
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            print("⏳ Loading WhisperModel...")
            _model = WhisperModel("tiny", compute_type="auto")  # you can also use "small"
            print("✅ WhisperModel loaded successfully.")
        except Exception as e:
            print("❌ Failed to load WhisperModel:", e)
            return None
    return _model

def transcribe_audio_file(audio_file):
    filename = secure_filename(audio_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(file_path)

    model = get_model()
    if model is None:
        # Return graceful error message if model failed to load
        return "Transcription model is currently unavailable."

    try:
        print("🔊 Transcribing with FasterWhisper:", file_path)
        segments, info = model.transcribe(file_path, beam_size=5, language="en")

        # Combine all segment texts
        transcription = " ".join(segment.text.strip() for segment in segments)
        print("✅ Transcription:", transcription)
        return transcription or "No text found"

    except Exception as e:
        print("❌ Error:", e)
        return "Transcription failed"

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print("🧹 File cleaned up.")
