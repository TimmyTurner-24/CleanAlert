import os
import secrets
from PIL import Image
from cleanalert import app
from flask_login import current_user, login_required
from flask import url_for, redirect

def save_picture(form_picture, pic_path):
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, pic_path, picture_fn)
    form_picture.save(picture_path)
    
    ouput_size = (360, 360)
    i = Image.open(form_picture)
    i.thumbnail(ouput_size)
    i.save(picture_path)
    
    return picture_fn

@login_required
def admin_required(func):
    def wrapper(*args, **kwargs):
        if current_user.role == 'admin':
            func(*args, **kwargs)
        else:
            if current_user.is_authenticated:
                return redirect(url_for('user_home'))
            return redirect(url_for('homepage'))
        
    return wrapper

@login_required
def resident_required(func):
    def wrapper(*args, **kwargs):
        if current_user.role == 'resident':
            func(*args, **kwargs)
        else:
            if current_user.is_authenticated:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('homepage'))
        
    return wrapper
