import os

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = (
            os.environ.get("DATABASE_URL")
            or os.environ.get("SQLALCHEMY_DATABASE_URI")
        )
        # Disable only for local development over plain HTTP.
        secure_cookies = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
        self.SESSION_COOKIE_SECURE = secure_cookies
        self.REMEMBER_COOKIE_SECURE = secure_cookies


def configure_database(app):
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Set SECRET_KEY to a long, random secret before starting CleanAlert.")
    uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        raise RuntimeError("Set DATABASE_URL to your PostgreSQL connection URL.")
    # Some hosting providers still issue the deprecated postgres:// scheme.
    if isinstance(uri, str) and uri.startswith("postgres://"):
        uri = "postgresql://" + uri[len("postgres://"):]
    try:
        url = make_url(uri)
        backend = url.get_backend_name()
        if backend == "postgresql":
            if url.drivername not in ("postgresql", "postgresql+psycopg2"):
                raise ValueError("unsupported PostgreSQL driver")
            url = url.set(drivername="postgresql+psycopg2")
        elif not (app.testing and backend == "sqlite"):
            raise ValueError("PostgreSQL required")
        # Force port validation without exposing credentials in errors.
        _ = url.port
    except (ArgumentError, ValueError, TypeError):
        raise RuntimeError("DATABASE_URL must be a valid PostgreSQL URL using psycopg2.") from None
    app.config["SQLALCHEMY_DATABASE_URI"] = url
