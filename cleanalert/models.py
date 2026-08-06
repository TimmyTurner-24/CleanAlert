from datetime import datetime
from cleanalert import db, login_manager
from flask_login import UserMixin

# Junction Table
admin_reports = db.Table(
    'admin_reports',
    db.Column('admin_id', db.Integer, db.ForeignKey('admin.id'), primary_key=True),
    db.Column('report_id', db.Integer, db.ForeignKey('report.id'), primary_key=True)
)

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
    reports = db.relationship('Report', backref='author', lazy=True)
    
    def __repr__(self):
        return f"Resident('{self.name}', '{self.email}', '{self.img}')"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    description = db.Column(db.Text, nullable=False, default='Exactly as category or image')
    location = db.Column(db.Text, nullable=False)
    img = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(10), nullable=False, default='pending')
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    def __repr__(self):
        return f"Report('{self.category}', '{self.date_posted}', '{self.location}')"
    
class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=True, nullable=False)
    img = db.Column(db.String(60), nullable=False, default="default.jpg")
    role = db.Column(db.String(10), default="admin")

    # Each admin can be linked to many reports (via the association table)
    reports = db.relationship('Report', secondary=admin_reports, lazy='subquery',
                              backref=db.backref('admins', lazy='dynamic'))

    def __repr__(self):
        return f"Admin('{self.name}', '{self.email}', '{self.img}')"
    