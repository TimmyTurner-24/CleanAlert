from pathlib import Path
import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from .config import Config, configure_database

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'users.sign_in'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    if config_class is Config:
        load_dotenv(Path(app.root_path).parent / ".env", override=False)
    app.config.from_object(config_class() if isinstance(config_class, type) else config_class)
    configure_database(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db, directory=str(Path(app.root_path).parent / "migrations"))

    from .users.routes import users
    from .main.routes import main
    from .reports.routes import reports
    from .users.admins.routes import admins
    from .users.residents.routes import residents

    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(reports)
    app.register_blueprint(admins)
    app.register_blueprint(residents)

    from .commands import register_commands
    register_commands(app)

    with app.app_context():
        # Create tables if missing
        db.create_all()

        # Create admin once from env vars (if set and not already present)
        from .models import User

        name = os.environ.get("ADMIN_NAME", "").strip()
        email = os.environ.get("ADMIN_EMAIL", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")

        if name and email and password.strip():
            if 3 <= len(name) <= 40 and len(password) >= 8:
                try:
                    email = validate_email(email, check_deliverability=False).normalized
                except EmailNotValidError:
                    email = ""

                if email and len(email) <= 120:
                    existing = User.query.filter(
                        (User.email == email) | (User.name == name)
                    ).all()
                    if not existing:
                        try:
                            db.session.add(User(
                                name=name,
                                email=email,
                                password=generate_password_hash(password),
                                role="admin",
                            ))
                            db.session.commit()
                        except IntegrityError:
                            db.session.rollback()

    return app
