from extensions import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone

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


