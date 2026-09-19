"""Environment-driven admin bootstrap used by deployments.

Kept separate from the app factory so the factory itself stays free of database
side effects: the schema is owned by Alembic, and creating rows is a separate
step that only runs once the schema actually exists.
"""
import os

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import generate_password_hash

from . import db
from .models import User

MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 40
MAX_EMAIL_LENGTH = 120
MIN_PASSWORD_LENGTH = 8
INITIAL_ADMIN_ROLE = "admin"


def _has_users_table():
    return inspect(db.engine).has_table(User.__tablename__)


def _read_credentials():
    return (
        os.environ.get("ADMIN_NAME", "").strip(),
        os.environ.get("ADMIN_EMAIL", "").strip(),
        os.environ.get("ADMIN_PASSWORD", ""),
    )


def bootstrap_admin(app):
    """Create the first admin from ADMIN_NAME, ADMIN_EMAIL and ADMIN_PASSWORD.

    Runs on every start but never updates or promotes an existing account, so
    the variables are safe to leave in a deployment environment. Does nothing
    at all when the three variables are not set.
    """
    name, email, password = _read_credentials()
    if not (name and email and password.strip()):
        return

    if not MIN_NAME_LENGTH <= len(name) <= MAX_NAME_LENGTH:
        app.logger.warning(
            "ADMIN_NAME must contain %s to %s characters; no admin was created.",
            MIN_NAME_LENGTH,
            MAX_NAME_LENGTH,
        )
        return
    if len(password) < MIN_PASSWORD_LENGTH:
        app.logger.warning(
            "ADMIN_PASSWORD must contain at least %s characters; no admin was created.",
            MIN_PASSWORD_LENGTH,
        )
        return
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        app.logger.warning("ADMIN_EMAIL is not a valid email address; no admin was created.")
        return
    if len(email) > MAX_EMAIL_LENGTH:
        app.logger.warning(
            "ADMIN_EMAIL must contain at most %s characters; no admin was created.",
            MAX_EMAIL_LENGTH,
        )
        return

    try:
        if not _has_users_table():
            app.logger.warning(
                "ADMIN_* variables are set but the '%s' table does not exist yet. "
                "Run 'flask --app main:app db upgrade' to create the schema.",
                User.__tablename__,
            )
            return
        _create_admin_if_missing(app, name, email, password)
    except SQLAlchemyError:
        # A missing or unreachable database must not stop the app from booting;
        # the developer needs the app up in order to run the migration.
        app.logger.warning(
            "Could not check or create the initial admin because the database is "
            "unavailable. Run 'flask --app main:app db upgrade' once it is reachable.",
            exc_info=True,
        )


def _create_admin_if_missing(app, name, email, password):
    existing = User.query.filter((User.email == email) | (User.name == name)).all()
    if existing:
        app.logger.info("An account already uses ADMIN_NAME or ADMIN_EMAIL; left unchanged.")
        return
    db.session.add(
        User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=INITIAL_ADMIN_ROLE,
        )
    )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        app.logger.info("An account already uses ADMIN_NAME or ADMIN_EMAIL; left unchanged.")
    else:
        app.logger.info("Initial admin account created from ADMIN_* environment variables.")
