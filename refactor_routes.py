import re
import os

app_py_path = r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\app.py'
with open(app_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Routes mapping
auth_funcs = ['welcome', 'register', 'login', 'logout']
upload_funcs = ['upload', 'preview_pdf', 'upload_submit', 'uploaded_preview', 'api_upload', 'api_delete_doc']
chatbot_funcs = ['dashboard', 'students', 'revoke_invite', 'profile', 'chat', 'transcribe_audio', 'speak', 'api_reset_db', 'api_ingest_website', 'api_db_stats', 'stream_response', 'api_knowledge_list', 'api_add_knowledge', 'api_delete_knowledge', 'resources', 'knowledge_base', 'admin_tools']

# Split the content at the first @app.route
route_start_match = re.search(r'\n@app\.route', content)
if not route_start_match:
    print("Could not find @app.route")
    exit(1)

start_idx = route_start_match.start()

header_app = content[:start_idx]
rest_of_app = content[start_idx:]

# Split rest_of_app at if __name__ ==
main_match = re.search(r'\nif __name__ ==', rest_of_app)
if main_match:
    routes_text = rest_of_app[:main_match.start()]
    main_text = rest_of_app[main_match.start():]
else:
    routes_text = rest_of_app
    main_text = ""

# Now split routes_text by @app.route
# To preserve the exact @app.route text, we use a trick: split by \n(?=@app\.route)
chunks = re.split(r'\n(?=@app\.route)', '\n' + routes_text)

app_code = []
auth_code = []
upload_code = []
chatbot_code = []

for chunk in chunks:
    if not chunk.strip():
        continue
    # Find the def function_name(
    match = re.search(r'def ([a-zA-Z0-9_]+)\(', chunk)
    if not match:
        app_code.append(chunk)
        continue
    
    func_name = match.group(1)
    
    route_match = re.search(r'@app\.route\((.*?)\)', chunk)
    if route_match:
        route_args = route_match.group(1)
        # Add endpoint explicitly
        if 'endpoint=' not in route_args:
            if route_args.strip() == '':
                # Should not happen but just in case
                new_route_args = f"endpoint='{func_name}'"
            else:
                new_route_args = route_args + f", endpoint='{func_name}'"
        else:
            new_route_args = route_args
            
        if func_name in auth_funcs:
            chunk = chunk.replace(route_match.group(0), f"@auth_bp.route({new_route_args})")
            auth_code.append(chunk)
        elif func_name in upload_funcs:
            chunk = chunk.replace(route_match.group(0), f"@upload_bp.route({new_route_args})")
            upload_code.append(chunk)
        elif func_name in chatbot_funcs:
            chunk = chunk.replace(route_match.group(0), f"@chatbot_bp.route({new_route_args})")
            chatbot_code.append(chunk)
        else:
            # Leave in app.py (e.g., favicon)
            app_code.append(chunk)
    else:
        app_code.append(chunk)

imports_block = """from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, stream_with_context, Response, send_from_directory, abort
from flask_login import login_required, login_user, logout_user, current_user
import os
import time
import json as json_lib
import fitz
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

"""

os.makedirs(r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\routes', exist_ok=True)

with open(r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\routes\auth.py', 'w', encoding='utf-8') as f:
    f.write(imports_block + "auth_bp = Blueprint('auth', __name__)\n" + ''.join(auth_code))

with open(r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\routes\upload.py', 'w', encoding='utf-8') as f:
    f.write(imports_block + "upload_bp = Blueprint('upload', __name__)\n" + ''.join(upload_code))

with open(r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\routes\chatbot.py', 'w', encoding='utf-8') as f:
    f.write(imports_block + "chatbot_bp = Blueprint('chatbot', __name__)\n" + ''.join(chatbot_code))

new_app_content = header_app + ''.join(app_code) + '\n\n'
new_app_content += """# ==========================================
# REGISTER BLUEPRINTS
# ==========================================
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.upload import upload_bp

app.register_blueprint(auth_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(upload_bp)
"""
new_app_content += main_text

with open(app_py_path, 'w', encoding='utf-8') as f:
    f.write(new_app_content)
    
print("Refactoring completed successfully.")
