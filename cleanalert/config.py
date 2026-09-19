import os
import sqlite3
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ArgumentError

POSTGRES_DRIVERS = ("postgresql", "postgresql+psycopg2")
SQLITE_OPT_IN_ENV_VAR = "ALLOW_SQLITE"

DATABASE_URL_ERROR = "DATABASE_URL must be a valid PostgreSQL URL using psycopg2."
UNSUPPORTED_BACKEND_ERROR = (
    "DATABASE_URL must point at PostgreSQL (postgresql://...): PostgreSQL is required "
    "outside tests. For local development set ALLOW_SQLITE=true and "
    "DATABASE_URL=sqlite:///cleanalert.db in your .env file."
)

_foreign_keys_listener_registered = False


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    # Production stays on PostgreSQL. Local development opts in to SQLite by
    # setting ALLOW_SQLITE=true, or automatically while running the test suite.
    ALLOW_SQLITE = False

    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = (
            os.environ.get("DATABASE_URL")
            or os.environ.get("SQLALCHEMY_DATABASE_URI")
        )
        self.ALLOW_SQLITE = (
            os.environ.get(SQLITE_OPT_IN_ENV_VAR, "").strip().lower() == "true"
        )
        # Disable only for local development over plain HTTP.
        secure_cookies = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
        self.SESSION_COOKIE_SECURE = secure_cookies
        self.REMEMBER_COOKIE_SECURE = secure_cookies


def _register_sqlite_foreign_keys():
    """Make SQLite enforce foreign keys the way PostgreSQL does.

    SQLite ignores foreign keys unless the pragma is enabled per connection, so
    local development would silently accept rows that production rejects.
    """
    global _foreign_keys_listener_registered
    if _foreign_keys_listener_registered:
        return

    @event.listens_for(Engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _foreign_keys_listener_registered = True


def _anchor_sqlite_path(app, url):
    """Place a relative SQLite file inside the instance folder.

    A relative SQLite URL resolves against the current working directory, so the
    database would appear to vanish when the app is started from a different
    directory. Anchoring it to instance_path keeps one database per project.
    """
    database = url.database
    if not database or database == ":memory:":
        return url
    path = Path(database)
    if not path.is_absolute():
        path = Path(app.instance_path) / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return url.set(database=str(path))


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
        # Force port validation without exposing credentials in errors.
        _ = url.port
    except (ArgumentError, ValueError, TypeError):
        raise RuntimeError(DATABASE_URL_ERROR) from None

    if backend == "postgresql":
        if url.drivername not in POSTGRES_DRIVERS:
            raise RuntimeError(DATABASE_URL_ERROR)
        url = url.set(drivername="postgresql+psycopg2")
    elif backend == "sqlite" and (app.testing or app.config.get("ALLOW_SQLITE")):
        url = _anchor_sqlite_path(app, url)
        _register_sqlite_foreign_keys()
        # pool_pre_ping is meaningless for SQLite and some pool classes reject it.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
    else:
        raise RuntimeError(UNSUPPORTED_BACKEND_ERROR)

    app.config["SQLALCHEMY_DATABASE_URI"] = url
