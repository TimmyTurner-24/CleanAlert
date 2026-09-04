from flask import Blueprint, flash, redirect, render_template, url_for
from werkzeug.security import generate_password_hash as gph
from ..forms import RegistrationForm
from ...models import User, Report
from ..utils import admin_required
from ... import db

admins = Blueprint('admins',__name__)

@admins.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template('Admin/dashboard.html',
        title='Admin Dashboard', total_residents=User.query.filter_by(role='resident').count(), total_reports=Report.query.count(), pending=Report.query.filter_by(status='pending').count(), in_progress=Report.query.filter_by(status='in progress').count(), resolved=Report.query.filter_by(status='resolved').count(), declined=Report.query.filter_by(status='declined').count())

@admins.route("/admin/new-admin", methods=['GET', 'POST'])
@admin_required
def create_admin():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = gph(form.password.data)
        user = User(name=form.name.data, email=form.email.data, password=hashed_password, role='admin')
        db.session.add(user)
        db.session.commit()
        flash('Admin successfully created!', 'success')
        return redirect(url_for('admins.admin_dashboard'))
    return render_template('register.html', title='Register New Admin', form=form, legend='Create New Admin')