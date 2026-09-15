from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
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
        db.create_all()

    return app
