import os
from flask import render_template, url_for, redirect, flash, request, abort
<<<<<<< HEAD
from .utils import save_picture, admin_required, resident_required, send_reset_email
from . import app, db
from .forms import LoginForm, RegistrationForm,UpdateAccountForm, ReportForm, UpdateReportStatus, RequestResetForm, ResetPasswordForm
=======
from .utils import save_picture, admin_required, resident_required
from . import app, db
from .forms import LoginForm, RegistrationForm,UpdateAccountForm, ReportForm, UpdateReportStatus
>>>>>>> 9ae30c1 (Getting ready for frontend)
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
    if current_user.is_authenticated:
        if current_user.role != 'admin':
            return redirect(url_for('user_home'))
        return redirect(url_for('admin_dashboard'))
    form = LoginForm()
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
<<<<<<< HEAD
=======

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
    return render_template('register.html', title='Register', form=form, legend='Register Now')

>>>>>>> 9ae30c1 (Getting ready for frontend)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@app.route("/reset_password", methods=['POST', 'GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with the code.', 'info')
        return redirect(url_for('sign_in'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    return render_template('reset_token.html', title='Reset Password', form=form)
# Resident routes

@app.route("/register", methods=['POST', 'GET']) # Creating an account defaults to Resident
def signup():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = gph(form.password.data)
        user = User(name=form.name.data.upper(), email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created!', 'success')
        return redirect(url_for('sign_in'))
    return render_template('register.html', title='Register', form=form, legend='Register Now')



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
        current_user.name = form.name.data.upper()
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
    page = request.args.get('page', 1, type=int)
<<<<<<< HEAD
    reports = Report.query.order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('Admin/report_stats.html', title='View all residents reports', reports=reports)
=======
    status = request.args.get('status', None)  # ← get filter from URL
    if status:
        # Filter by status
        reports = Report.query.filter_by(status=status).order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    else:
        # Show all reports
        reports = Report.query.order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('Admin/report_stats.html', title='All Reports', reports=reports, current_status=status)
>>>>>>> 9ae30c1 (Getting ready for frontend)

@app.route("/admin/update-report/<int:report_id>", methods=['GET', 'POST'])
@admin_required
def update_status(report_id):
    report = Report.query.get_or_404(report_id)
    form = UpdateReportStatus()
    if form.validate_on_submit():
<<<<<<< HEAD
        if report.status == 'in progress' or report.status == 'pending':
            report.status = form.status.data
            db.session.commit()
            flash('The report status has been updated!', 'success')
            return redirect(url_for('admin_report_view'))
=======
        report.status = form.status.data
        db.session.commit()
        flash('The report status has been updated!', 'success')
        return redirect(url_for('admin_report_view'))
>>>>>>> 9ae30c1 (Getting ready for frontend)
    return render_template('Admin/update_status_report.html', title='View all residents reports', report=report, form=form)

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
<<<<<<< HEAD
    return render_template('Admin/dashboard.html', title='Admin Dashboard', total_residents=User.query.filter_by(role='resident').count(), total_reports=Report.query.count(), pending_reports=Report.query.filter_by(status='pending').count())
=======
    return render_template('Admin/dashboard.html',
        title='Admin Dashboard', total_residents=User.query.filter_by(role='resident').count(), total_reports=Report.query.count(), pending=Report.query.filter_by(status='pending').count(), in_progress=Report.query.filter_by(status='in progress').count(), resolved=Report.query.filter_by(status='resolved').count(), declined=Report.query.filter_by(status='declined').count())
>>>>>>> 9ae30c1 (Getting ready for frontend)

@app.route("/admin/new-admin", methods=['GET', 'POST'])
@admin_required
def create_admin():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = gph(form.password.data)
<<<<<<< HEAD
        user = User(name=form.name.data.upper(), email=form.email.data, password=hashed_password, role='admin')
=======
        user = User(name=form.name.data, email=form.email.data, password=hashed_password, role='admin')
>>>>>>> 9ae30c1 (Getting ready for frontend)
        db.session.add(user)
        db.session.commit()
        flash('Admin successfully created!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('register.html', title='Register New Admin', form=form, legend='Create New Admin')