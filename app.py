from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies

db = SQLAlchemy(app)

# Initialize the LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

bcrypt = Bcrypt(app)

from routes import *  # Import routes after initializing app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)