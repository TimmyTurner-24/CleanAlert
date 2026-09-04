from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'users.sign_in'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    
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
    
    return app