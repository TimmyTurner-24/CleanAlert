import os

import click
from email_validator import EmailNotValidError, validate_email
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from . import db
from .models import User


def register_commands(app):
    @app.cli.command("create-admin")
    def create_admin():
        """Create the initial admin using ADMIN_NAME, ADMIN_EMAIL and ADMIN_PASSWORD."""
        name = os.environ.get("ADMIN_NAME", "").strip()
        email = os.environ.get("ADMIN_EMAIL", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not name or not email or not password.strip():
            raise click.ClickException("Set ADMIN_NAME, ADMIN_EMAIL and ADMIN_PASSWORD first.")
        if not 3 <= len(name) <= 40:
            raise click.ClickException("ADMIN_NAME must contain 3 to 40 characters.")
        if len(password) < 12:
            raise click.ClickException("ADMIN_PASSWORD must contain at least 12 characters.")
        try:
            email = validate_email(email, check_deliverability=False).normalized
        except EmailNotValidError:
            raise click.ClickException("ADMIN_EMAIL must be a valid email address.") from None
        if len(email) > 120:
            raise click.ClickException("ADMIN_EMAIL must contain at most 120 characters.")

        existing = User.query.filter((User.email == email) | (User.name == name)).all()
        if existing:
            if len(existing) == 1 and existing[0].role == "admin" and existing[0].email == email and existing[0].name == name:
                click.echo("Admin already exists; credentials left unchanged.")
                return
            raise click.ClickException("Name or email already belongs to an account; no account was changed.")

        db.session.add(User(name=name, email=email, password=generate_password_hash(password), role="admin"))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise click.ClickException("An account with that name or email already exists.") from None
        click.echo("Admin created. Sign in at /login using ADMIN_EMAIL and your password.")
