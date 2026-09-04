from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash as gph

from cleanalert import db
from cleanalert.models import Report, User
from ..utils import resident_required
from ..forms import RegistrationForm

residents = Blueprint('residents',__name__)

@residents.route("/register", methods=['POST', 'GET']) # Creating an account defaults to Resident
def signup():
    form = RegistrationForm()
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admins.admin_dashboard'))
        elif current_user.role == 'resident':
            return redirect(url_for('residents.user_home'))
    if form.validate_on_submit():
        hashed_password = gph(form.password.data)
        user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created!', 'success')
        return redirect(url_for('users.sign_in'))
    return render_template('register.html', title='Register', form=form, legend='Register Now')

@residents.route("/dashboard")
@login_required
def user_home():
    if current_user.role == 'admin':
        return redirect(url_for('admins.admin_dashboard'))
    return render_template('Resident/dashboard.html', title='Dashboard')
