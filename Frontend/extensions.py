from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

login_manager.login_view = 'auth.login'  # Updated to point to blueprint route
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
