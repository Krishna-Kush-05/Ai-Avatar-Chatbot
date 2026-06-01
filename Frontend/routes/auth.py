from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, stream_with_context, Response, send_from_directory, abort
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

auth_bp = Blueprint('auth', __name__)
@auth_bp.route("/", endpoint='welcome')
def welcome():
    if current_user.is_authenticated:
        if current_user.role in ['teacher', 'institute']:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('chat'))
    return render_template('welcome.html', title='Welcome')
@auth_bp.route("/register", methods=['GET', 'POST'], endpoint='register')
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

        if user.role in ['teacher', 'institute']:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('chat'))

    role = request.args.get('role', 'student')
    form.role.data = role

    # Prefill email if provided in request args (e.g. from invitation link)
    email = request.args.get('email', '')
    if email and request.method == 'GET':
        form.email.data = email

    return render_template('register.html', title='Register', form=form, role=role.title())
@auth_bp.route("/login", methods=['GET', 'POST'], endpoint='login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Check if they are an invited placeholder trying to log in
        if user and user.role == 'student_invited':
            flash('You have been invited! Please register your account to set a password and get started.', 'info')
            return redirect(url_for('register', role='student'))

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.get_display_name()}!', 'success')
            next_page = request.args.get('next')

            if user.role in ['teacher', 'institute']:
                return redirect(next_page or url_for('dashboard'))
            else:
                return redirect(next_page or url_for('chat'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)
@auth_bp.route("/logout", endpoint='logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- CORE APPLICATION ROUTES ---
