# app.py (Imports at the top)
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory, stream_with_context, Response
from transcribe import transcribe_audio_file
from datetime import datetime, timezone
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
import os
from tts import generate_audio
import requests
from services import api_client
from services.tts_service import generate_tts_audio

from flask_cors import CORS

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Email service import removed


# --- NEW IMPORTS FOR AUTH & FORMS ---
# --- END NEW IMPORTS ---


app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdfs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')


from extensions import db, bcrypt, login_manager
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)


# --- AUTHENTICATION & WELCOME ROUTES ---
@app.route('/favicon.ico')
def favicon():
    return '', 204

# ─────────────────────────────────────────────────────────────
# KNOWLEDGE BASE PROXY ROUTES
# ─────────────────────────────────────────────────────────────


# ==========================================
# REGISTER BLUEPRINTS
# ==========================================
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.upload import upload_bp

app.register_blueprint(auth_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(upload_bp)

if __name__ == "__main__":
    # Ensure all necessary directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'previews'), exist_ok=True)
    os.makedirs('static/audio', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)

    with app.app_context():
        db.create_all() # This creates/updates all tables (User, Chatbot, UploadedPDF)
    app.run(debug=True, threaded=True)  # threaded=True → supports concurrent users
