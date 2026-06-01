# app.py (Imports at the top)
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory, stream_with_context, Response
from transcribe import transcribe_audio_file
from flask_sqlalchemy import SQLAlchemy
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

# Email service import
from email_service import send_onboarding_email


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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 👈 NEW: Relationship to uploaded PDFs
    pdfs = db.relationship('UploadedPDF', backref='chatbot', lazy=True, cascade="all, delete-orphan")
    #   NEW: For "coming soon" website links
    website_url = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"Chatbot('{self.name}', '{self.domain}')"

# --- UPDATED: UploadedPDF Model ---
class UploadedPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
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
