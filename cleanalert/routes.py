import secrets, os
from flask import render_template, url_for, redirect, flash, request
from PIL import Image
from cleanalert import app, db
from cleanalert.forms import LoginForm, RegistrationForm,UpdateAccountForm, ReportForm
from cleanalert.models import Resident, Report
from werkzeug.security import generate_password_hash as gph, check_password_hash as cph
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
def homepage():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html', title='about')

@app.route("/register", methods=['POST', 'GET'])
def signup():
    form = RegistrationForm()
    if current_user.is_authenticated:
        return redirect(url_for(user_home))
    if form.validate_on_submit():
        hashed_password = gph(form.password.data)
        resident = Resident(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(resident)
        db.session.commit()
        flash('Account successfully created!', 'success')
        return redirect(url_for('sign_in'))
    return render_template('Resident/register.html', title='Register', form=form)

@app.route("/login", methods=['POST', 'GET'])
def sign_in():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('user_home'))
    if form.validate_on_submit():
        resident = Resident.query.filter_by(email=form.email.data).first()
        if resident and cph(resident.password, form.password.data):
            login_user(resident, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('user_home'))
        else:
            flash('Invalid email address or password', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@app.route("/dashboard")
@login_required
def user_home():
    return render_template('Resident/dashboard.html', title='Dashboard')

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

@app.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'static/profile_pics')
            if current_user.img != 'default.jpg':
                rm_pic_path = os.path.join(app.root_path, 'static/profile_pics', current_user.img)
                os.remove(rm_pic_path)
            current_user.img = picture_file
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
    img_file = url_for('static', filename=f'profile_pics/{current_user.img}')
    return render_template('Resident/account.html', title='Account', img_file=img_file, form=form)

@app.route("/report", methods=['GET', 'POST'])
@login_required
def make_report():
    form = ReportForm()
    if form.validate_on_submit():
        upload_file = ''
        if form.upload.data:
            upload_file = save_picture(form.upload.data, 'static/uploads')
        report = Report(category=form.category.data, description=form.description.data, location=form.location.data, img=upload_file, author=current_user)
        db.session.add(report)
        db.session.commit()
        flash('Your complaint has been sent!', 'success')
        return redirect(url_for('view_reports'))
    return render_template('Resident/mk_report.html', title='Make Report', form=form)

@app.route("/my-reports")
@login_required
def view_reports():
    pass

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('homepage'))