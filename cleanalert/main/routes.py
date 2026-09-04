from flask import Blueprint, render_template, url_for, redirect
from flask_login import current_user

main = Blueprint('main',__name__)

@main.route("/")
def homepage():
    if current_user.is_authenticated:
        if current_user.role == 'resident':
            return redirect(url_for('residents.user_home'))
        elif current_user.role == 'admin':
            return redirect(url_for('admins.admin_dashboard'))
    return render_template('home.html')

@main.route("/about")
def about():
    return render_template('about.html', title='About')