# app.py (Imports at the top)
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
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
import httpx  # Instead of requests
from flask import stream_with_context, Response

# --- NEW IMPORTS FOR AUTH & FORMS ---
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, URL
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
# --- END NEW IMPORTS ---


app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdfs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a-very-secret-key-you-must-change' # 👈 ADD THIS

db = SQLAlchemy(app)
bcrypt = Bcrypt(app) # 👈 ADD THIS
login_manager = LoginManager(app) # 👈 ADD THIS
login_manager.login_view = 'login' # 👈 Page to redirect to
login_manager.login_message = 'Please log in to access this page.' # 👈 Flash message
login_manager.login_message_category = 'info' # 👈 Flash message category

# --- NEW: User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- UPDATED: User Model ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True, default='New User') # 👈 NEW: Full name
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # Roles: 'teacher', 'professional', 'institute', 'student', 'student_invited' (placeholder)
    role = db.Column(db.String(50), nullable=False)

    institution = db.Column(db.String(200), nullable=True) # 👈 NEW: Institution/Org

    # 👈 NEW: Link for tracking who invited a student
    invited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    chatbots = db.relationship('Chatbot', backref='owner', lazy=True, cascade="all, delete-orphan")
    
    # 👈 NEW: For a teacher to see their *invited* students (placeholders)
    # This finds Users where 'invited_by_id' matches this user's 'id'
    invited_users_placeholders = db.relationship('User', 
                                     backref=db.backref('inviter', remote_side=[id]), 
                                     lazy='dynamic',
                                     foreign_keys=[invited_by_id])

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    # 👈 NEW: Helper to show 'Name' or 'Username'
    def get_display_name(self):
        return self.name if self.name and self.name != 'New User' else self.username

# --- UPDATED: Chatbot Model ---
class Chatbot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    domain = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 👈 NEW: Relationship to uploaded PDFs
    pdfs = db.relationship('UploadedPDF', backref='chatbot', lazy=True, cascade="all, delete-orphan")
    # 👈 NEW: For "coming soon" website links
    website_url = db.Column(db.String(500), nullable=True) 

    def __repr__(self):
        return f"Chatbot('{self.name}', '{self.domain}')"

# --- UPDATED: UploadedPDF Model ---
class UploadedPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    file_size_kb = db.Column(db.Integer, nullable=True)
    pages = db.Column(db.Integer, nullable=True)
    # 👈 REMOVED: session_id (no longer needed)
    
    # 👈 NEW: Link PDF to a *specific chatbot*, not just a user
    chatbot_id = db.Column(db.Integer, db.ForeignKey('chatbot.id'), nullable=False)


# --- NEW: Flask-WTF Forms ---

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)]) # 👈 NEW
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = HiddenField('Role', validators=[DataRequired()])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        # Allow validation *if* it's just an invited placeholder, but not if it's an active user
        if user and user.role not in ['student_invited']:
            raise ValidationError('That email is already in use by an active account.')

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# 👈 NEW: Form for Profile Page
class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address (Read-Only)', validators=[DataRequired(), Email()], render_kw={'readonly': True})
    username = StringField('Username (Read-Only)', validators=[DataRequired()], render_kw={'readonly': True})
    institution = StringField('Institution / Organization', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Update Profile')

# 👈 NEW: Form for Dashboard (Bot Config)
class BotConfigForm(FlaskForm):
    bot_name = StringField('Assistant Name', validators=[DataRequired(), Length(max=100)])
    bot_desc = TextAreaField('Purpose / Description', validators=[Optional(), Length(max=500)])
    bot_domain = SelectField('Domain', choices=[
        ('education', 'Education'),
        ('corporate', 'Corporate'),
        ('support', 'Customer Support'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    website_url = StringField('Website URL (Coming Soon)', validators=[Optional(), URL(message="Please enter a valid URL (e.g., http://example.com)")])
    submit_bot = SubmitField('Activate Assistant')

# 👈 NEW: Form for Dashboard (Invite Student)
class InviteStudentForm(FlaskForm):
    student_email = StringField('Student Email Address', validators=[DataRequired(), Email()])
    submit_invite = SubmitField('Invite Student')

# 👈 NEW: Form for Dashboard (Organization)
class OrganizationForm(FlaskForm):
    institution_name = StringField('Institution / Organization Name', validators=[DataRequired(), Length(max=200)])
    submit_org = SubmitField('Save Details')
    
# --- AUTHENTICATION & WELCOME ROUTES ---

@app.route("/")
def welcome():
    if current_user.is_authenticated:
        if current_user.role in ['teacher', 'professional', 'institute']:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('chat'))
    return render_template('welcome.html', title='Welcome')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if email is from an invited placeholder
        invited_placeholder = User.query.filter_by(email=form.email.data, role='student_invited').first()
        
        user = None # Initialize user to None

        if invited_placeholder:
            # --- CORRECTED LOGIC: UPDATE THE PLACEHOLDER ---
            user = invited_placeholder # Assign the existing placeholder to 'user'
            user.name = form.name.data
            user.username = form.username.data
            user.set_password(form.password.data) # Set the new password
            user.role = form.role.data # Change role from 'student_invited' to 'student'
            # invited_by_id is already correctly set on the placeholder
            # No need to db.session.add(user) as it's an existing object
        else:
            # This is a normal (non-invited) registration
            user = User(
                name=form.name.data, 
                username=form.username.data, 
                email=form.email.data, 
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user) # Only add if it's a completely new user
        
        db.session.commit() # Commit the changes (either update or add)
        
        login_user(user)
        flash(f'Account created for {user.get_display_name()}! You are now logged in.', 'success')
        
        if user.role in ['teacher', 'professional', 'institute']:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('chat'))
            
    role = request.args.get('role', 'student')
    form.role.data = role
    
    return render_template('register.html', title='Register', form=form, role=role.title())

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.get_display_name()}!', 'success')
            next_page = request.args.get('next')
            
            if user.role in ['teacher', 'professional', 'institute']:
                return redirect(next_page or url_for('dashboard'))
            else:
                return redirect(next_page or url_for('chat'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- CORE APPLICATION ROUTES ---

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.role not in ['teacher', 'professional', 'institute']:
        flash('You do not have permission to access that page.', 'warning')
        return redirect(url_for('chat'))
        
    # Create instances of all forms for the dashboard
    bot_form = BotConfigForm(prefix='bot')
    invite_form = InviteStudentForm(prefix='invite')
    org_form = OrganizationForm(prefix='org')
    
    # --- Handle Bot Configuration Form Submission ---
    if bot_form.submit_bot.data and bot_form.validate_on_submit():
        new_bot = Chatbot(
            name=bot_form.bot_name.data,
            description=bot_form.bot_desc.data,
            domain=bot_form.bot_domain.data,
            website_url=bot_form.website_url.data if bot_form.website_url.data else None, # 👈 NEW
            owner=current_user
        )
        db.session.add(new_bot)
        db.session.commit()
        flash(f'New AI Assistant "{new_bot.name}" has been configured and activated!', 'success')
        return redirect(url_for('dashboard')) # Redirect to clear form
        
    # --- Handle Student Invitation Form Submission ---
    if invite_form.submit_invite.data and invite_form.validate_on_submit():
        student_email = invite_form.student_email.data
        
        # Check if email is already an active user
        existing_active_user = User.query.filter_by(email=student_email).filter(User.role.in_(['student', 'teacher', 'professional', 'institute'])).first()
        if existing_active_user:
            flash(f'A user with this email ({student_email}) is already an active member.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Check if email is already invited by *anyone*
        existing_invited_user = User.query.filter_by(email=student_email, role='student_invited').first()
        if existing_invited_user:
            flash(f'This email ({student_email}) has already been invited. They need to register to activate their account.', 'info')
            return redirect(url_for('dashboard'))

        # Create a placeholder invite entry
        invite_placeholder = User(
            username=f"invited_{student_email.split('@')[0]}_{datetime.now().strftime('%H%M%S')}", # Unique username
            email=student_email,
            password_hash=bcrypt.generate_password_hash("!INVALID_PASSWORD_PLACEHOLDER!").decode('utf-8'), # A dummy hash
            role='student_invited',
            invited_by_id=current_user.id
        )
        db.session.add(invite_placeholder)
        db.session.commit()
        flash(f'Invitation sent to {student_email}. They can now register using this email.', 'success')
        return redirect(url_for('dashboard'))
            
    # --- Handle Organization Details Form Submission ---
    if org_form.submit_org.data and org_form.validate_on_submit():
        current_user.institution = org_form.institution_name.data
        db.session.commit()
        flash('Organization details updated successfully.', 'success')
        return redirect(url_for('dashboard'))

    # --- On GET request, pre-fill forms and fetch data ---
    org_form.institution_name.data = current_user.institution
    
    # Fetch data for dashboard
    user_bots = Chatbot.query.filter_by(user_id=current_user.id).order_by(Chatbot.created_at.desc()).all()
    
    # Fetch invited students (placeholders)
    invited_students_placeholders = current_user.invited_users_placeholders.filter_by(role='student_invited').all()
    
    # Fetch active students (who have registered)
    active_students = User.query.filter_by(invited_by_id=current_user.id, role='student').all()

    return render_template(
        'dashboard.html', 
        title='Creator Dashboard', 
        bots=user_bots,
        invited_students=invited_students_placeholders, # 👈 NEW
        active_students=active_students, # 👈 NEW
        bot_form=bot_form,
        invite_form=invite_form,
        org_form=org_form
    )

# 👈 --- NEW: Profile Page Route ---
@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.institution = form.institution.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile'))
    
    # Pre-fill the form with existing data on GET request
    form.name.data = current_user.name
    form.email.data = current_user.email
    form.username.data = current_user.username
    form.institution.data = current_user.institution
    
    instructor = None
    if current_user.role == 'student' and current_user.invited_by_id:
        instructor = User.query.get(current_user.invited_by_id)
        
    return render_template('profile.html', title='My Profile', form=form, instructor=instructor)

# --- CHAT & KNOWLEDGE BASE ROUTES ---

@app.route("/chat")
@login_required
def chat():
    # This just renders the chat page. The old PDF sidebar logic is removed.
    # We will later add logic to select *which* bot to chat with.
    return render_template("index.html", title='AI Chat Assistant')

# 👈 NEW: /knowledge/upload route
@app.route("/knowledge/upload", methods=["GET"])
@login_required
def upload():
    # Fetch user's bots to populate the dropdown
    user_bots = Chatbot.query.filter_by(user_id=current_user.id).all()
    if not user_bots:
        flash('You must configure an AI Assistant before you can upload knowledge.', 'warning')
        return redirect(url_for('dashboard'))
        
    return render_template("upload.html", title='Upload Knowledge', bots=user_bots)

# --- UPDATED: /upload/preview route ---
@app.route("/upload/preview", methods=["POST"])
@login_required
def preview_pdf():
    pdf_file = request.files.get("pdf")
    chatbot_id = request.form.get("chatbot_id") # 👈 Get selected bot ID
    user_bots = Chatbot.query.filter_by(user_id=current_user.id).all()

    if not pdf_file:
        flash("No file selected for upload.", 'danger')
        return render_template("upload.html", title='Upload Knowledge', bots=user_bots)
    if not chatbot_id:
        flash("You must select an AI Assistant to link this knowledge to.", 'danger')
        return render_template("upload.html", title='Upload Knowledge', bots=user_bots, error="You must select an assistant.")

    # Send file to backend FastAPI /upload endpoint
    backend_url = "http://127.0.0.1:8000/upload"
    files = {"files": (pdf_file.filename, pdf_file.stream, pdf_file.mimetype)}
    try:
        resp = requests.post(backend_url, files=files, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            flash(f"Upload successful: {result.get('message', '')}", 'success')
        else:
            flash(f"Upload failed: {resp.text}", 'danger')
    except Exception as e:
        flash(f"Error uploading to backend: {str(e)}", 'danger')

    # No local save, no preview image
    return render_template("upload.html", title='Upload Knowledge', bots=user_bots, selected_bot_id=int(chatbot_id))

# --- UPDATED: /upload/submit route ---
@app.route("/upload/submit", methods=["POST"])
@login_required
def upload_submit():
    # 👈 Link PDF to the selected chatbot
    new_pdf = UploadedPDF(
        filename=request.form["filename"],
        filepath=request.form["filepath"],
        file_size_kb=int(request.form["filesize"]),
        pages=int(request.form["pages"]),
        chatbot_id=int(request.form["chatbot_id"]) # 👈 Save the bot ID
    )
    db.session.add(new_pdf)
    db.session.commit()
    
    flash(f'File "{request.form["filename"]}" uploaded successfully.', 'success')
    return redirect(url_for('dashboard')) # Redirect to dashboard after upload


# --- API / UTILITY ROUTES ---

# 👈 NEW: Custom route to serve preview images from the UPLOADS folder
@app.route('/uploads/previews/<filename>')
def uploaded_preview(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'previews'), filename)

@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400
    audio_file = request.files["audio"]
    try:
        text = transcribe_audio_file(audio_file)
        return jsonify({"transcribedText": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/speak", methods=["POST"])
def speak():
    text = request.json.get("text", "")
    audio_path = generate_audio(text)
    if audio_path:
        return jsonify({"audio_url": url_for('static', filename='audio/output.mp3')})
    else:
        return jsonify({"error": "TTS failed"}), 500

# 👈 Set your FastAPI URL here
BASE_FASTAPI_URL = "http://127.0.0.1:8000" # Example: "http://127.0.0.1:8000"

@app.route("/stream_response", methods=["POST"])
def stream_response():
    question = request.json.get("question")
    if not question:
        return jsonify({"error": "Missing question"}), 400

    import json as json_lib
    
    @stream_with_context
    def generate():
        try:
            # You might want to pass more context here, like the current chatbot_id
            with requests.post(
                BASE_FASTAPI_URL + "/query",
                json={"question": question}, stream=True, timeout=120 # Increased timeout
            ) as response:
                if response.status_code != 200:
                    yield f"data: {json_lib.dumps({'text': f'[ERROR]: Upstream returned {response.status_code}. Check the AI service.'})}\n\n"
                    return

                event_type = ""
                for line in response.iter_lines(decode_unicode=True):
                    if not line.strip():
                        continue
                    
                    # Parse the incoming SSE format from backend
                    if line.startswith("event:"):
                        event_type = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        try:
                            data_json = json_lib.loads(line[len("data:"):].strip())
                            text_chunk = data_json.get("text", "")
                            
                            # Forward with event type included
                            yield f"event: {event_type}\ndata: {json_lib.dumps({'text': text_chunk})}\n\n"
                        except json_lib.JSONDecodeError:
                            continue
        except requests.exceptions.ConnectionError:
            yield f"data: {json_lib.dumps({'text': '[ERROR]: Could not connect to the AI service. Please ensure it is running on port 8000.'})}\n\n"
        except requests.exceptions.Timeout:
            yield f"data: {json_lib.dumps({'text': '[ERROR]: The AI service timed out. Please try again.'})}\n\n"
        except Exception as e:
            yield f"data: {json_lib.dumps({'text': f'[ERROR]: {str(e)}'})}\n\n"
    return Response(generate(), content_type='text/event-stream')

@app.route('/favicon.ico')
def favicon():
    return '', 204

# --- NEW: Placeholder Routes for Sidebar Navigation ---
@app.route("/resources")
@login_required
def resources():
    return render_template("resources.html", title="Resources/Documents")

@app.route("/knowledge_base")
@login_required
def knowledge_base():
    return render_template("knowledge_base.html", title="Knowledge Base")

@app.route("/admin_tools")
@login_required
def admin_tools():
    return render_template("admin.html", title="Admin Tools")

# --- App Execution ---
if __name__ == "__main__":
    # Ensure all necessary directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'previews'), exist_ok=True)
    os.makedirs('static/audio', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)

    with app.app_context():
        db.create_all() # This creates/updates all tables (User, Chatbot, UploadedPDF)
    app.run(debug=True)