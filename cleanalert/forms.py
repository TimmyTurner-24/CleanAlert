from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, EmailField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User
from flask_login import current_user

class RegistrationForm(FlaskForm):
    name = StringField('Fullname', validators=[DataRequired(), Length(min=2, max=30)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_name(self, name):
        user = User.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('This name is already taken. Please use another')
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is in use. Please use another')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')
    
class UpdateAccountForm(FlaskForm):
    name = StringField('Fullname', validators=[DataRequired(), Length(min=2, max=30)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')
    
    def validate_name(self, name):
        if name.data != current_user.name:
            user = User.query.filter_by(name=name.data).first()
            if user:
                raise ValidationError('This name is already taken. Please use another')
        
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email is in use. Please use another')

class ReportForm(FlaskForm):
    category = SelectField('Category', validators=[DataRequired()], choices=['Sewage',
                                                                             'Dumping',
                                                                             'Overfull (Roadblockage)',
                                                                             'Stinking',
                                                                             'Others'])
    description = TextAreaField('Description', validators=[DataRequired()])
    upload = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    location = StringField('Location', validators=[DataRequired()])
    submit = SubmitField('Submit Report')
    
class UpdateReportStatus(FlaskForm):
    status = SelectField('Status', validators=[DataRequired()], choices=['in progress',
                                                                         'declined',
                                                                         'resolved'])
    submit = SubmitField('Update Status')
    
class ResetPasswordForm(FlaskForm):
    pass

class RequestResetForm(FlaskForm):
    pass