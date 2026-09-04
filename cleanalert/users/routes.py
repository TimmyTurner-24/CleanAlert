import os

from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash as cph
from cleanalert import db
from ..models import User
from .forms import LoginForm, UpdateAccountForm
from .utils import save_picture

users = Blueprint('users',__name__)

@users.route("/login", methods=['POST', 'GET'])
def sign_in():
    if current_user.is_authenticated:
        if current_user.role != 'admin':
            return redirect(url_for('residents.user_home'))
        return redirect(url_for('admins.admin_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and cph(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admins.admin_dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('residents.user_home'))
        flash('Invalid email address or password', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@users.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'static/profile_pics')
            if current_user.img != 'default.jpg':
                rm_pic_path = os.path.join(current_app.root_path, 'static/profile_pics', current_user.img)
                os.remove(rm_pic_path)
            current_user.img = picture_file
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
    img_file = url_for('static', filename=f'profile_pics/{current_user.img}')
    return render_template('account.html', title='Account', img_file=img_file, form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.homepage'))