from datetime import datetime, timezone
<<<<<<< HEAD
from itsdangerous import URLSafeTimedSerializer as Serializer
=======
# from itsdangerous import URLSafeTimedSerializer as Serializer
>>>>>>> 9ae30c1 (Getting ready for frontend)
from . import db, login_manager, app
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
    
<<<<<<< HEAD
    def get_reset_token(self, expire_sec=600):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_token(token, expire_sec=600):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expire_sec)
        except:
            return None
        return User.query.get(user_id)
=======
    # def get_reset_token(self, expire_sec=600):
    #     s = Serializer(app.config['SECRET_KEY'])
    #     return s.dumps({'user_id': self.id})
    
    # @staticmethod
    # def verify_reset_token(token, expire_sec=600):
    #     s = Serializer(app.config['SECRET_KEY'])
    #     try:
    #         user_id = s.loads(token, max_age=expire_sec)
    #     except:
    #         return None
    #     return User.query.get(user_id)
>>>>>>> 9ae30c1 (Getting ready for frontend)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.img}', '{self.role}')"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text, nullable=False)
    img = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # no admin_id, no junction table
    def __repr__(self):
        return f"Report('{self.category}', '{self.status}')"