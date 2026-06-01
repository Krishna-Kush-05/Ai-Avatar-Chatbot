from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, URL
from models import User

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

pass

class EmptyForm(FlaskForm):
    pass
