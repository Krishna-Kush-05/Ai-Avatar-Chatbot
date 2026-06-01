from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, stream_with_context, Response, send_from_directory, abort
from flask_login import login_required, login_user, logout_user, current_user
import os
import time
import json as json_lib
import fitz
import requests
from datetime import datetime
from werkzeug.utils import secure_filename

# Models and Forms
from extensions import db, bcrypt
from models import User, Chatbot, UploadedPDF
from forms import RegistrationForm, LoginForm, ProfileForm, BotConfigForm, InviteStudentForm, OrganizationForm, EmptyForm
from utils.workspace import _get_workspace_id

# Services
from services import api_client
from services.tts_service import generate_tts_audio
from services.email_service import send_invitation_email
from transcribe import transcribe_audio_file

chatbot_bp = Blueprint('chatbot', __name__)
@chatbot_bp.route("/dashboard", methods=['GET', 'POST'], endpoint='dashboard')
@login_required
def dashboard():
    if current_user.role not in ['teacher', 'institute']:
        flash('You do not have permission to access that page.', 'warning')
        return redirect(url_for('chatbot.chat'))

    bot_form = BotConfigForm(prefix='bot')
    org_form = OrganizationForm(prefix='org')

    # --- Handle Bot Configuration Form Submission ---
    if bot_form.submit_bot.data and bot_form.validate_on_submit():
        new_bot = Chatbot(
            name=bot_form.bot_name.data,
            description=bot_form.bot_desc.data,
            domain=bot_form.bot_domain.data,
            website_url=bot_form.website_url.data if bot_form.website_url.data else None,
            owner=current_user
        )
        db.session.add(new_bot)
        db.session.commit()
        flash(f'New AI Assistant "{new_bot.name}" has been configured and activated!', 'success')
        return redirect(url_for('chatbot.dashboard'))

    # --- Handle Organization Details Form Submission ---
    if org_form.submit_org.data and org_form.validate_on_submit():
        current_user.institution = org_form.institution_name.data
        db.session.commit()
        flash('Organization details updated successfully.', 'success')
        return redirect(url_for('chatbot.dashboard'))

    # Pre-fill org form
    org_form.institution_name.data = current_user.institution

    user_bots = Chatbot.query.filter_by(user_id=current_user.id).order_by(Chatbot.created_at.desc()).all()

    return render_template(
        'dashboard.html',
        title='Creator Dashboard',
        bots=user_bots,
        bot_form=bot_form,
        org_form=org_form
    )

@chatbot_bp.route("/students", methods=['GET', 'POST'], endpoint='students')
@login_required
def students():
    if current_user.role not in ['teacher', 'institute']:
        flash('You do not have permission to access that page.', 'warning')
        return redirect(url_for('chatbot.chat'))

    invite_form = InviteStudentForm(prefix='invite')

    if request.method == 'POST' and invite_form.validate_on_submit():
        student_email = invite_form.student_email.data

        existing_active_user = User.query.filter_by(email=student_email).filter(
            User.role.in_(['student', 'teacher', 'professional', 'institute'])
        ).first()
        if existing_active_user:
            flash(f'A user with this email ({student_email}) is already an active member.', 'warning')
            return redirect(url_for('chatbot.students'))

        existing_invited_user = User.query.filter_by(email=student_email, role='student_invited').first()
        if existing_invited_user:
            flash(f'This email ({student_email}) has already been invited.', 'info')
            return redirect(url_for('chatbot.students'))

        invite_placeholder = User(
            username=f"invited_{student_email.split('@')[0]}_{datetime.now().strftime('%H%M%S')}",
            email=student_email,
            password_hash=bcrypt.generate_password_hash("!INVALID_PASSWORD_PLACEHOLDER!").decode('utf-8'),
            role='student_invited',
            invited_by_id=current_user.id
        )
        db.session.add(invite_placeholder)
        db.session.commit()

        # Send onboarding email to the student
        try:
            registration_url = url_for('auth.register', role='student', email=student_email, _external=True)
            inviter_name = current_user.get_display_name()
            inviter_institution = current_user.institution

            email_sent = send_invitation_email(
                to_email=student_email,
                invite_link=registration_url
            )
            if email_sent:
                flash(f'Invitation sent to {student_email}. An onboarding email has been sent successfully.', 'success')
            else:
                flash(f'Invitation saved for {student_email}, but we failed to send the onboarding email. Please check SMTP logs.', 'warning')
        except Exception as e:
            print(f"[ERROR] Failed to send invitation email: {e}")
            flash(f'Invitation saved for {student_email}, but email sending failed: {str(e)}', 'warning')

        return redirect(url_for('chatbot.students'))

    invited_students = current_user.invited_users_placeholders.filter_by(role='student_invited').all()
    active_students = User.query.filter_by(invited_by_id=current_user.id, role='student').all()

    from flask_wtf import FlaskForm
    class EmptyForm(FlaskForm):
        pass
    revoke_form = EmptyForm()

    return render_template(
        'students.html',
        title='Student Management',
        invite_form=invite_form,
        invited_students=invited_students,
        active_students=active_students,
        revoke_csrf=lambda: revoke_form.hidden_tag()
    )

@chatbot_bp.route("/students/revoke/<int:invite_id>", methods=['POST'], endpoint='revoke_invite')
@login_required
def revoke_invite(invite_id):
    if current_user.role not in ['teacher', 'institute']:
        flash('Permission denied.', 'warning')
        return redirect(url_for('chatbot.chat'))
    invite = User.query.get_or_404(invite_id)
    if invite.invited_by_id != current_user.id or invite.role != 'student_invited':
        flash('You cannot revoke this invitation.', 'danger')
        return redirect(url_for('chatbot.students'))
    db.session.delete(invite)
    db.session.commit()
    flash(f'Invitation for {invite.email} has been revoked.', 'success')
    return redirect(url_for('chatbot.students'))

# 👈 --- NEW: Profile Page Route ---
@chatbot_bp.route("/profile", methods=['GET', 'POST'], endpoint='profile')
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.institution = form.institution.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('chatbot.profile'))

    # Pre-fill the form with existing data on GET request
    if request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.username.data = current_user.username
        form.institution.data = current_user.institution

    instructor = None
    if current_user.role == 'student' and current_user.invited_by_id:
        instructor = User.query.get(current_user.invited_by_id)

    return render_template('profile.html', title='My Profile', form=form, instructor=instructor)

# --- CHAT & KNOWLEDGE BASE ROUTES ---
@chatbot_bp.route("/chat", endpoint='chat')
@login_required
def chat():
    # This just renders the chat page. The old PDF sidebar logic is removed.
    # We will later add logic to select *which* bot to chat with.
    return render_template("index.html", title='AI Chat Assistant')

# 👈 NEW: /knowledge/upload route
@chatbot_bp.route("/transcribe", methods=["POST"], endpoint='transcribe_audio')
def transcribe_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400
    audio_file = request.files["audio"]
    try:
        text = transcribe_audio_file(audio_file)
        return jsonify({"transcribedText": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@chatbot_bp.route("/speak", methods=["POST"], endpoint='speak')
@login_required
def speak():
    """
    TTS endpoint: Uses the central tts_service.
    """
    text = request.json.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    audio_filename = generate_tts_audio(text)
    
    if audio_filename:
        return jsonify({
            "audio_url": url_for('static', filename=f'audio/{audio_filename}')
        })

    return jsonify({"error": "TTS failed"}), 500

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────




# ═══════════════════════════════════════════════════════════════
# FLASK PROXY API LAYER
# All backend calls go through /api/* → no CORS issues in browser
# workspace_id is injected into every request automatically
# ═══════════════════════════════════════════════════════════════
@chatbot_bp.route("/api/reset_db", methods=["POST"], endpoint='api_reset_db')
@login_required
def api_reset_db():
    """
    Proxy: HARD reset → FastAPI POST /reset_db
    Deletes: files + vector embeddings + Q&A pairs.
    NOT a re-index — this is a full wipe of the teacher's workspace.
    """
    workspace_id = _get_workspace_id()
    try:
        resp = api_client.reset_db(workspace_id)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend unreachable"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chatbot_bp.route("/api/ingest_website", methods=["POST"], endpoint='api_ingest_website')
@login_required
def api_ingest_website():
    """Proxy: ingest a website URL → FastAPI POST /ingest/website  (workspace-isolated)."""
    workspace_id = _get_workspace_id()
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "url field is required"}), 400
    try:
        resp = api_client.ingest_website(url, workspace_id)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend unreachable"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chatbot_bp.route("/api/db_stats", endpoint='api_db_stats')
@login_required
def api_db_stats():
    """
    Proxy: DB statistics → FastAPI GET /db_stats  (workspace-filtered).
    IMPORTANT: This route is defined BEFORE app.run() to avoid 404.
    """
    workspace_id = _get_workspace_id()
    try:
        resp = api_client.get_db_stats(workspace_id)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend unreachable"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# STREAM RESPONSE  (updated: injects workspace_id)
# ─────────────────────────────────────────────────────────────
@chatbot_bp.route("/stream_response", methods=["POST"], endpoint='stream_response')
@login_required
def stream_response():
    question = request.json.get("question")
    if not question:
        return jsonify({"error": "Missing question"}), 400

    # Inject workspace_id so the teacher's RAG context is used
    workspace_id = _get_workspace_id()

    import json as json_lib

    @stream_with_context
    def generate():
        try:
            with api_client.send_query({"question": question, "workspace_id": workspace_id}) as response:
                if response.status_code != 200:
                    yield f"data: {json_lib.dumps({'text': f'[ERROR]: Upstream returned {response.status_code}.'})}\n\n"
                    return

                event_type = ""
                for line in response.iter_lines(decode_unicode=True):
                    if not line.strip():
                        continue
                    if line.startswith("event:"):
                        event_type = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        try:
                            data_json = json_lib.loads(line[len("data:"):].strip())
                            text_chunk = data_json.get("text", "")
                            yield f"event: {event_type}\ndata: {json_lib.dumps({'text': text_chunk})}\n\n"
                        except json_lib.JSONDecodeError:
                            continue
        except requests.exceptions.ConnectionError:
            yield f"data: {json_lib.dumps({'text': '[ERROR]: Could not connect to AI service.'})}\n\n"
        except requests.exceptions.Timeout:
            yield f"data: {json_lib.dumps({'text': '[ERROR]: AI service timed out.'})}\n\n"
        except Exception as e:
            yield f"data: {json_lib.dumps({'text': f'[ERROR]: {str(e)}'})}\n\n"

    return Response(generate(), content_type='text/event-stream')
@chatbot_bp.route("/api/knowledge", methods=["GET"], endpoint='api_knowledge_list')
@login_required
def api_knowledge_list():
    """Proxy: list all Q&A pairs for this workspace → FastAPI GET /knowledge."""
    workspace_id = _get_workspace_id()
    try:
        resp = api_client.get_knowledge(workspace_id)
        from flask import make_response
        response = make_response(jsonify(resp.json()), resp.status_code)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend unreachable"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chatbot_bp.route("/api/add_knowledge", methods=["POST"], endpoint='api_add_knowledge')
@login_required
def api_add_knowledge():
    """Proxy: add a Q&A pair → FastAPI POST /add_knowledge (workspace-isolated)."""
    workspace_id = _get_workspace_id()
    data = request.get_json(silent=True) or {}
    data["workspace_id"] = workspace_id
    print(f"[DEBUG /api/add_knowledge] workspace_id={workspace_id!r}, data={data}")
    try:
        resp = api_client.add_knowledge(data)
        print(f"[DEBUG /api/add_knowledge] FastAPI status={resp.status_code}, body={resp.text[:200]}")
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        print("[DEBUG /api/add_knowledge] ConnectionError - FastAPI unreachable")
        return jsonify({"error": "Backend unreachable"}), 502
    except Exception as e:
        print(f"[DEBUG /api/add_knowledge] Exception: {e}")
        return jsonify({"error": str(e)}), 500

@chatbot_bp.route("/api/delete_knowledge/<int:kid>", methods=["DELETE"], endpoint='api_delete_knowledge')
@login_required
def api_delete_knowledge(kid):
    """Proxy: delete a Q&A pair → FastAPI DELETE /knowledge/<id>."""
    workspace_id = _get_workspace_id()
    try:
        resp = api_client.delete_knowledge(kid, workspace_id)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend unreachable"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- NEW: Placeholder Routes for Sidebar Navigation ---
@chatbot_bp.route("/resources", endpoint='resources')
@login_required
def resources():
    return render_template("resources.html", title="Resources/Documents")
@chatbot_bp.route("/knowledge_base", endpoint='knowledge_base')
@login_required
def knowledge_base():
    if current_user.role not in ['teacher', 'institute']:
        flash('You do not have permission to access the knowledge base.', 'warning')
        return redirect(url_for('chatbot.chat'))
    return render_template("knowledge_base.html", title="Knowledge Base")
@chatbot_bp.route("/admin_tools", endpoint='admin_tools')
@login_required
def admin_tools():
    return render_template("admin.html", title="Admin Tools")

# --- App Execution ---