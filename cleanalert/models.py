from datetime import datetime
from cleanalert import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_resident(resident_id):
    return Resident.query.get(int(resident_id))

class Resident(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=True, nullable=False)
    img = db.Column(db.String(60), nullable=False, default="default.jpg")
    role = db.Column(db.String(10), default="resident")
    reports = db.relationship("Report", backref="author", lazy=True)
    
    def __repr__(self):
        return f"Resident('{self.name}', '{self.email}', '{self.img}')"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    img = db.Column(db.String(60), nullable=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'), nullable=False)
    def __repr__(self):
        return f"Report('{self.category}', '{self.date_posted}', '{self.description}', '{self.location}')"
    
# class Admin(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(40), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password = db.Column(db.String(60), unique=True, nullable=False)
#     img = db.Column(db.String(60), nullable=False, default="default.jpg")
#     role = db.Column(db.String(10), default="admin")
#     reports = db.relationship("Report", backref="admin", lazy=True)
#     def __repr__(self):
#         return f"Admin('{self.name}', '{self.email}', '{self.img}')"
    