from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, EmailField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from cleanalert.models import Resident
from flask_login import current_user

class RegistrationForm(FlaskForm):
    name = StringField('Fullname', validators=[DataRequired(), Length(min=2, max=30)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_name(self, name):
        resident = Resident.query.filter_by(name=name.data).first()
        if resident:
            raise ValidationError('This name is already taken. Please use another')
        
    def validate_email(self, email):
        resident = Resident.query.filter_by(email=email.data).first()
        if resident:
            raise ValidationError('This email is in use. Please use another')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')
    
class UpdateAccountForm(FlaskForm):
    name = StringField('Fullname', validators=[DataRequired(), Length(min=2, max=30)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update')
    
    def validate_name(self, name):
        if name.data != current_user.name:
            resident = Resident.query.filter_by(name=name.data).first()
            if resident:
                raise ValidationError('This name is already taken. Please use another')
        
    def validate_email(self, email):
        if email.data != current_user.email:
            resident = Resident.query.filter_by(email=email.data).first()
            if resident:
                raise ValidationError('This email is in use. Please use another')