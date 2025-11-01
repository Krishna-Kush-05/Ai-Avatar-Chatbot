from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, stream_with_context
from transcribe import transcribe_audio_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
import os
from tts import generate_audio
from flask import send_from_directory
import requests  # 🔁 For calling Krishna’s FastAPI from Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdfs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# URL of Krishna’s FastAPI query endpoint
BASE_FASTAPI_URL = "http://127.0.0.1:8000"

class UploadedPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    file_size_kb = db.Column(db.Integer, nullable=True)
    pages = db.Column(db.Integer, nullable=True)
    session_id = db.Column(db.String(100), nullable=True)

@app.route("/")
def index():
    all_pdfs = UploadedPDF.query.order_by(UploadedPDF.upload_time.desc()).all()
    return render_template("index.html", pdfs=all_pdfs)

@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400
    audio_file = request.files["audio"]
    try:
        text = transcribe_audio_file(audio_file)
        response = {"transcribedText": text}
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

os.makedirs("uploads", exist_ok=True)
os.makedirs("static/previews", exist_ok=True)

@app.route("/upload", methods=["GET"])
def upload():
    return render_template("upload.html")

@app.route("/upload/preview", methods=["POST"])
def preview_pdf():
    pdf_file = request.files["pdf"]
    if not pdf_file:
        return "No file uploaded", 400
    filename = secure_filename(pdf_file.filename)
    filepath = os.path.join("uploads", filename)
    pdf_file.save(filepath)
    doc = fitz.open(filepath)
    page = doc.load_page(0)
    pix = page.get_pixmap()
    preview_name = filename.rsplit('.', 1)[0] + "_preview.png"
    preview_path = os.path.join("static/previews", preview_name)
    pix.save(preview_path)
    return render_template("upload.html",
                           preview_path=url_for('static', filename=f"previews/{preview_name}"),
                           filename=filename,
                           filepath=filepath,
                           filesize=os.path.getsize(filepath) // 1024,
                           pages=len(doc))

@app.route("/upload/submit", methods=["POST"])
def upload_submit():
    new_pdf = UploadedPDF(
        filename=request.form["filename"],
        filepath=request.form["filepath"],
        file_size_kb=int(request.form["filesize"]),
        pages=int(request.form["pages"])
    )
    db.session.add(new_pdf)
    db.session.commit()
    return redirect("/")

@app.route("/speak", methods=["POST"])
def speak():
    text = request.json.get("text", "")
    audio_path = generate_audio(text)
    if audio_path:
        return jsonify({"audio_url": url_for('static', filename='audio/output.mp3')})
    else:
        return jsonify({"error": "TTS failed"}), 500

# --- ✅ THIS IS THE CORRECTED FUNCTION ---
@app.route("/stream_response", methods=["POST"])
def stream_response():
    question = request.json.get("question")
    if not question:
        return jsonify({"error": "Missing question"}), 400

    def generate():
        """A generator function that proxies the stream."""
        try:
            with requests.post(
                f"{BASE_FASTAPI_URL}/query",
                json={"question": question},
                stream=True,
                timeout=60
            ) as response:
                if response.status_code != 200:
                    error_message = response.text
                    yield f"event: final_response\ndata: {{\"text\": \"Error from backend: {error_message}\"}}\n\n"
                    return
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to backend: {e}")
            yield f"event: final_response\ndata: {{\"text\": \"Error: Could not connect to the AI service.\"}}\n\n"
            
    return Response(stream_with_context(generate()), content_type='text/event-stream')


@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == "__main__":
    app.run(debug=True)