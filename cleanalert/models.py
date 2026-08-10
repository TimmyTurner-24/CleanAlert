from datetime import datetime, timezone
from . import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    if not user_id:
        return None
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    img = db.Column(db.String(60), nullable=False, default='default.jpg')
    role = db.Column(db.String(10), nullable=False, default='resident')
    reports = db.relationship('Report', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.img}', '{self.role}')"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text, nullable=False)
    img = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(10), nullable=False, default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # no admin_id, no junction table
    def __repr__(self):
        return f"Report('{self.category}', '{self.status}')"