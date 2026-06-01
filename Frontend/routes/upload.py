from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, stream_with_context, Response, send_from_directory, abort, current_app
from flask_login import login_required, login_user, logout_user, current_user
import os
import time
import json as json_lib
import fitz
import requests
from datetime import datetime
from werkzeug.utils import secure_filename

# Models and Forms
from app import db, bcrypt, User, Chatbot, UploadedPDF
from app import RegistrationForm, LoginForm, ProfileForm, BotConfigForm, InviteStudentForm, OrganizationForm, EmptyForm
from app import _get_workspace_id

# Services
from services import api_client
from services.tts_service import generate_tts_audio
from email_service import send_onboarding_email
from transcribe import transcribe_audio_file

upload_bp = Blueprint('upload', __name__)
@upload_bp.route("/knowledge/upload", methods=["GET"], endpoint='upload')
@login_required
def upload():
    # Fetch user's bots to populate the dropdown
    user_bots = Chatbot.query.filter_by(user_id=current_user.id).all()
    if not user_bots:
        flash('You must configure an AI Assistant before you can upload knowledge.', 'warning')
        return redirect(url_for('dashboard'))

    return render_template("upload.html", title='Upload Knowledge', bots=user_bots)

# --- UPDATED: /upload/preview route ---@upload_bp.route("/upload/preview", methods=["POST"], endpoint='preview_pdf')
@login_required
def preview_pdf():
    pdf_file = request.files.get("pdf")
    chatbot_id = request.form.get("chatbot_id")
    user_bots = Chatbot.query.filter_by(user_id=current_user.id).all()

    if not pdf_file or pdf_file.filename == '':
        flash("No file selected for upload.", 'danger')
        return render_template("upload.html", title='Upload Knowledge', bots=user_bots)
    if not chatbot_id:
        flash("You must select an AI Assistant to link this knowledge to.", 'danger')
        return render_template("upload.html", title='Upload Knowledge', bots=user_bots, error="You must select an assistant.")

    filename = secure_filename(pdf_file.filename)

    # Save file temporarily so we can read it with fitz & send to backend
    os.makedirs('static/previews', exist_ok=True)
    temp_path = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    pdf_file.save(temp_path)

    # --- Generate preview image using PyMuPDF ---
    preview_path = None
    pages = 0
    try:
        doc = fitz.open(temp_path)
        pages = len(doc)
        page = doc[0]
        mat = fitz.Matrix(1.5, 1.5)  # 1.5x zoom for good quality
        pix = page.get_pixmap(matrix=mat)
        preview_filename = filename.rsplit('.', 1)[0] + '_preview.png'
        preview_save_path = os.path.join('static', 'previews', preview_filename)
        pix.save(preview_save_path)
        preview_path = f"/static/previews/{preview_filename}"
        doc.close()
    except Exception as e:
        flash(f"Could not generate preview: {str(e)}", 'warning')

    # Get file size in KB
    filesize = round(os.path.getsize(temp_path) / 1024)

    # --- Send file to FastAPI backend ---
    try:
        with open(temp_path, 'rb') as f:
            resp = api_client.upload_files(files={"files": (filename, f, "application/pdf")}, workspace_id=_get_workspace_id())
        if resp.status_code == 200:
            result = resp.json()
            flash(f"Upload successful: {result.get('message', '')}", 'success')
        else:
            flash(f"Upload failed (backend): {resp.text}", 'danger')
    except Exception as e:
        flash(f"Could not reach AI backend: {str(e)}", 'warning')

    return render_template(
        "upload.html",
        title='Upload Knowledge',
        bots=user_bots,
        selected_bot_id=int(chatbot_id),
        preview_path=preview_path,
        filename=filename,
        filepath=temp_path,
        filesize=filesize,
        pages=pages
    )


# --- UPDATED: /upload/submit route ---@upload_bp.route("/upload/submit", methods=["POST"], endpoint='upload_submit')
@login_required
def upload_submit():
    from flask import abort
    chatbot_id = int(request.form["chatbot_id"])
    
    # Verify that the chatbot belongs to the current user
    chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user.id).first()
    if not chatbot:
        abort(403)

    # 👈 Link PDF to the selected chatbot
    new_pdf = UploadedPDF(
        filename=request.form["filename"],
        filepath=request.form["filepath"],
        file_size_kb=int(request.form["filesize"]),
        pages=int(request.form["pages"]),
        chatbot_id=chatbot_id # 👈 Save the bot ID
    )
    db.session.add(new_pdf)
    db.session.commit()

    flash(f'File "{request.form["filename"]}" uploaded successfully.', 'success')
    return redirect(url_for('dashboard')) # Redirect to dashboard after upload


# --- API / UTILITY ROUTES ---

# 👈 NEW: Custom route to serve preview images from the UPLOADS folder@upload_bp.route('/uploads/previews/<filename>', endpoint='uploaded_preview')
def uploaded_preview(filename):
    return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER'], 'previews'), filename)
@upload_bp.route("/api/upload", methods=["POST"], endpoint='api_upload')
@login_required
def api_upload():
    """Proxy: upload documents → FastAPI /upload  (workspace-isolated)."""
    workspace_id = _get_workspace_id()
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    multipart = [("files", (f.filename, f.stream, f.mimetype)) for f in files]
    try:
        resp = api_client.upload_files(files=multipart, workspace_id=workspace_id)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend unreachable. Is FastAPI running on port 8000?"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@upload_bp.route("/api/delete_doc", methods=["DELETE"], endpoint='api_delete_doc')
@login_required
def api_delete_doc():
    """Proxy: delete a single document → FastAPI DELETE /raw_docs  (workspace-isolated)."""
    workspace_id = _get_workspace_id()
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "filename parameter required"}), 400
    try:
        resp = api_client.delete_raw_doc(filename, workspace_id)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend unreachable"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

