import os
from datetime import datetime, timezone
from flask import render_template, url_for, redirect, flash, request, abort
from .utils import save_picture, admin_required, resident_required
from . import app, db
from .forms import LoginForm, RegistrationForm,UpdateAccountForm, ReportForm
from .models import User, Report
from werkzeug.security import generate_password_hash as gph, check_password_hash as cph
from flask_login import login_user, current_user, logout_user, login_required

# Open routes / Multiple users allowed but different routes
@app.route("/")
def homepage():
    return render_template('home.html')
@app.route("/home")
def home():
    return redirect(url_for('homepage'))

@app.route("/login", methods=['POST', 'GET'])
def sign_in():
    form = LoginForm()
    if current_user.is_authenticated:
        if current_user.role != 'admin':
            return redirect(url_for('user_home'))
        return redirect(url_for('admin_dashboard'))
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and cph(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('user_home'))
        flash('Invalid email address or password', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/dashboard")
@login_required
def user_home():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('Resident/dashboard.html', title='Dashboard')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('homepage'))

# Resident routes

@app.route("/register", methods=['POST', 'GET']) # Creating an account defaults to Resident
def signup():
    form = RegistrationForm()
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_home'))
    if form.validate_on_submit():
        hashed_password = gph(form.password.data)
        user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created!', 'success')
        return redirect(url_for('sign_in'))
    return render_template('Resident/register.html', title='Register', form=form)



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
@resident_required
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
    elif request.method == 'GET':
        form.description.data = 'Exactly as category'
    return render_template('Resident/mk_report.html', title='Make Report', form=form)

@app.route("/my-reports")
@resident_required
def view_reports():
    page = request.args.get('page', 1, type=int)
    reports = Report.query.filter_by(author=current_user).order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('Resident/view_report.html', title='My Reports', reports=reports)

@app.route("/report/<int:report_id>", methods=['GET', 'POST'])
@resident_required
def update_report(report_id):
    report = Report.query.get_or_404(report_id)
    # if report.status != 'pending':
    #     return redirect(url_for)
    if report.author != current_user:
        abort(403)
    form = ReportForm()
    if form.validate_on_submit():
        report.category = form.category.data
        report.description = form.description.data
        report.location = form.location.data
        if form.upload.data:
            if report.img:
                rm_pic_path = os.path.join(app.root_path, 'static/uploads', report.img)
                os.remove(rm_pic_path)
            report.img = save_picture(form.upload.data, 'static/uploads')
        db.session.commit()
        flash('Your report has been updated', 'success')
        return redirect(url_for('view_reports'))
    elif request.method == 'GET':
        form.category.data = report.category
        form.description.data = report.description
        form.location.data = report.location
    return render_template('Resident/mk_report.html', title='Update Report', form=form)

@app.route("/report/<int:report_id>/delete", methods=['POST'])
@resident_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    # if report.status != 'pending':
    #     return redirect(url_for)
    if report.author != current_user:
        abort(403)
    db.session.delete(report)
    db.session.commit()
    flash('Your report has been deleted', 'success')
    return redirect(url_for('view_reports'))
        
# Admin routes

@app.route("/admin/reports")
@admin_required
def admin_report_view():
    # if current_user.role != 'admin':
    #     return redirect(url_for('user_home'))
    page = request.args.get('page', 1, type=int)
    reports = Report.query.order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('Admin/report_stats.html', title='View all residents reports', reports=reports)

@app.route("/admin/update-report")
@admin_required
def update_status():
    if current_user.role != 'admin':
        return redirect(url_for('user_home'))
    return render_template('Admin/update_status_report.html', title='View all residents reports', reports=Report.query.all())

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('user_home'))
    return render_template('Admin/dashboard.html', title='Admin Dashboard', total_residents=len(User.query.filter_by(role='resident').all()), total_reports=len(Report.query.all()), pending_reports=len(Report.query.filter_by(status='pending').all()))
