import os
import secrets
from PIL import Image
from cleanalert import app


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