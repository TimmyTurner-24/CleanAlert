import os
import secrets
from re import search
from functools import wraps
from PIL import Image
from cleanalert import app
from flask_login import current_user
from flask import url_for, redirect, abort
from wtforms.validators import StopValidation

def save_picture(form_picture, pic_path):
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, pic_path, picture_fn)
    form_picture.save(picture_path)
    
    output_size = (360, 360)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('sign_in'))
        if current_user.role == 'admin':
            return func(*args, **kwargs)
        abort(403)
    return wrapper

def resident_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('sign_in'))
        if current_user.role == 'resident':
            return func(*args, **kwargs)
        abort(403)
    return wrapper

class StrongPassword:
    def __init__(self, message:str=None):
        self.message = message
    
    def __call__(self, form, field):
        data = field.data
        # self.field_flags = {}
        if not search(r'[A-Z]', data):
            if self.message:
                raise StopValidation(message=self.message)
            raise StopValidation('Password must contain an uppercase letter')
        if not search(r'[a-z]', data):
            if self.message:
                raise StopValidation(message=self.message)
            raise StopValidation('Password must contain a lowercase letter')
        if not search(r'[0-9]', data):
            if self.message:
                raise StopValidation(message=self.message)
            raise StopValidation('Password must contain a number')