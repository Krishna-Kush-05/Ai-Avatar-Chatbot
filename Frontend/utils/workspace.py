from flask_login import current_user
from models import User, Chatbot

def _get_workspace_id():
    """Returns the current teacher's workspace_id (their email)."""
    if not current_user.is_authenticated:
        return "default"

    # If the user is a student, their workspace belongs to the teacher who invited them
    if current_user.role == 'student' and current_user.invited_by_id:
        teacher = User.query.get(current_user.invited_by_id)
        if teacher:
            return teacher.email

    return current_user.email

