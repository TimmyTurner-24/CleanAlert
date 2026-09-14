"""Run with python -m unittest discover -s tests -v.

Optionally set TEST_DATABASE_URL to a PostgreSQL test database. Every test uses
an isolated temporary schema; the database user needs permission to create it.
"""
import io
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask import Flask
from flask_migrate import downgrade, upgrade
from PIL import Image
from sqlalchemy import inspect, text
from werkzeug.datastructures import FileStorage
from werkzeug.security import check_password_hash

from cleanalert import create_app, db
from cleanalert.config import Config, configure_database
from cleanalert.models import Report, User
from cleanalert.users.utils import save_picture


class ConfigurationTests(unittest.TestCase):
    def configure(self, uri, testing=False):
        app = Flask(__name__)
        app.config.update(SECRET_KEY="test-only", SQLALCHEMY_DATABASE_URI=uri, TESTING=testing)
        configure_database(app)
        return app

    def test_postgres_schemes_and_ssl_are_preserved(self):
        for scheme in ("postgres", "postgresql", "postgresql+psycopg2"):
            with self.subTest(scheme=scheme):
                app = self.configure(f"{scheme}://name:p%40ss@localhost:5432/db?sslmode=require")
                url = app.config["SQLALCHEMY_DATABASE_URI"]
                self.assertEqual(url.drivername, "postgresql+psycopg2")
                self.assertEqual(url.password, "p@ss")
                self.assertEqual(url.query["sslmode"], "require")

    def test_database_url_takes_precedence(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql:///new", "SQLALCHEMY_DATABASE_URI": "sqlite:///old.db"}, clear=True):
            self.assertEqual(Config().SQLALCHEMY_DATABASE_URI, "postgresql:///new")

    def test_legacy_environment_variable(self):
        with patch.dict(os.environ, {"SQLALCHEMY_DATABASE_URI": "postgresql:///legacy"}, clear=True):
            self.assertEqual(Config().SQLALCHEMY_DATABASE_URI, "postgresql:///legacy")

    def test_missing_database_is_actionable(self):
        with self.assertRaisesRegex(RuntimeError, "Set DATABASE_URL"):
            self.configure(None)

    def test_missing_secret_is_actionable(self):
        with self.assertRaisesRegex(RuntimeError, "Set SECRET_KEY"):
            configure_database(Flask(__name__))

    def test_sqlite_is_only_allowed_in_tests(self):
        with self.assertRaisesRegex(RuntimeError, "PostgreSQL"):
            self.configure("sqlite:///:memory:")
        self.configure("sqlite:///:memory:", testing=True)

    def test_bad_urls_do_not_leak_credentials(self):
        for uri in ("mysql://name:private-secret@host/db", "postgresql://name:private-secret@host:invalid/db", "invalid", "postgresql+psycopg://name:private-secret@host/db"):
            with self.subTest(uri=uri), self.assertRaises(RuntimeError) as caught:
                self.configure(uri)
            self.assertNotIn("private-secret", str(caught.exception))

    def test_secure_cookies_default_and_local_override(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(Config().SESSION_COOKIE_SECURE)
            self.assertTrue(Config().REMEMBER_COOKIE_SECURE)
        with patch.dict(os.environ, {"COOKIE_SECURE": "false"}, clear=True):
            self.assertFalse(Config().SESSION_COOKIE_SECURE)

    def test_configuration_is_read_at_app_creation(self):
        with patch.dict(os.environ, {"SECRET_KEY": "test-only", "DATABASE_URL": "postgresql:///first"}, clear=True):
            self.assertEqual(create_app().config["SQLALCHEMY_DATABASE_URI"].database, "first")
            os.environ["DATABASE_URL"] = "postgresql:///second"
            self.assertEqual(create_app().config["SQLALCHEMY_DATABASE_URI"].database, "second")

    def test_postgresql_migration_sql(self):
        with patch.dict(os.environ, {"SECRET_KEY": "test-only", "DATABASE_URL": "postgresql:///test"}, clear=True):
            result = create_app().test_cli_runner().invoke(args=["db", "upgrade", "--sql"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("password VARCHAR(255)", result.output)
        self.assertIn("FOREIGN KEY(user_id) REFERENCES users (id)", result.output)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.schema = "test_" + uuid4().hex
        database_url = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
        self.postgres = database_url.startswith(("postgres://", "postgresql"))

        class TestConfig:
            TESTING = True
            SECRET_KEY = "test-only"
            SQLALCHEMY_DATABASE_URI = database_url
            WTF_CSRF_ENABLED = False
            SESSION_COOKIE_SECURE = False
            SQLALCHEMY_TRACK_MODIFICATIONS = False

        config = TestConfig()
        if self.postgres:
            config.SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"options": f"-csearch_path={self.schema}"}}
        self.app = create_app(config)
        self.context = self.app.app_context()
        self.context.push()
        if self.postgres:
            with db.engine.begin() as connection:
                connection.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        upgrade()
        self.client = self.app.test_client()
        self.credentials = {"ADMIN_NAME": "Test Administrator", "ADMIN_EMAIL": "admin@example.com", "ADMIN_PASSWORD": "test-only-long-password"}

    def tearDown(self):
        db.session.remove()
        if self.postgres:
            with db.engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
        db.engine.dispose()
        self.context.pop()

    def bootstrap(self, **overrides):
        values = {**self.credentials, **overrides}
        with patch.dict(os.environ, values):
            return self.app.test_cli_runner().invoke(args=["create-admin"])

    def test_migrations_match_models_and_can_be_repeated(self):
        upgrade()
        with db.engine.connect() as connection:
            migration_context = MigrationContext.configure(connection)
            self.assertEqual(compare_metadata(migration_context, db.metadata), [])
        self.assertIn("report", inspect(db.engine).get_table_names())
        downgrade(revision="base")
        self.assertNotIn("users", inspect(db.engine).get_table_names())
        upgrade()
        self.assertIn("users", inspect(db.engine).get_table_names())

    def test_bootstrap_hash_and_admin_login(self):
        result = self.bootstrap()
        self.assertEqual(result.exit_code, 0, result.output)
        admin = User.query.one()
        self.assertEqual(admin.role, "admin")
        self.assertNotIn(self.credentials["ADMIN_PASSWORD"], result.output)
        self.assertNotEqual(admin.password, self.credentials["ADMIN_PASSWORD"])
        self.assertTrue(check_password_hash(admin.password, self.credentials["ADMIN_PASSWORD"]))
        self.assertLessEqual(len(admin.password), 255)
        response = self.client.post("/login", data={"email": admin.email, "password": self.credentials["ADMIN_PASSWORD"]}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, "/admin/dashboard")

    def test_bootstrap_does_not_reset_password(self):
        self.assertEqual(self.bootstrap().exit_code, 0)
        original = User.query.one().password
        result = self.bootstrap(ADMIN_PASSWORD="different-test-password")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("unchanged", result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.one().password, original)

    def test_bootstrap_requires_all_credentials(self):
        for key in self.credentials:
            with self.subTest(key=key):
                self.assertNotEqual(self.bootstrap(**{key: ""}).exit_code, 0)
        self.assertEqual(User.query.count(), 0)

    def test_invalid_admin_details_are_rejected(self):
        for overrides in ({"ADMIN_NAME": "ab"}, {"ADMIN_NAME": "x" * 41}, {"ADMIN_EMAIL": "invalid"}, {"ADMIN_PASSWORD": "short"}, {"ADMIN_PASSWORD": " " * 12}):
            with self.subTest(overrides=overrides):
                self.assertNotEqual(self.bootstrap(**overrides).exit_code, 0)
        self.assertEqual(User.query.count(), 0)

    def test_existing_resident_is_never_promoted(self):
        db.session.add(User(name="Resident", email=self.credentials["ADMIN_EMAIL"], password="unchanged", role="resident"))
        db.session.commit()
        self.assertNotEqual(self.bootstrap().exit_code, 0)
        resident = User.query.one()
        self.assertEqual(resident.role, "resident")
        self.assertEqual(resident.password, "unchanged")

    def test_conflicting_name_is_not_overwritten(self):
        self.assertEqual(self.bootstrap().exit_code, 0)
        self.assertNotEqual(self.bootstrap(ADMIN_EMAIL="other@example.com").exit_code, 0)
        self.assertEqual(User.query.one().email, self.credentials["ADMIN_EMAIL"])

    def test_public_pages_load(self):
        for path in ("/", "/about", "/login", "/register"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.client.get("/admin/dashboard").status_code, 302)

    def test_resident_registration_and_access_control(self):
        response = self.client.post("/register", data={"name": "Test Resident", "email": "resident@example.com", "password": "resident-test-pass", "confirm_password": "resident-test-pass"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.query.one().role, "resident")
        self.client.post("/login", data={"email": "resident@example.com", "password": "resident-test-pass"})
        self.assertEqual(self.client.get("/admin/dashboard").status_code, 403)

    def test_registration_rejects_overlong_postgres_values(self):
        response = self.client.post("/register", data={"name": "x" * 41, "email": "resident@example.com", "password": "resident-test-pass", "confirm_password": "resident-test-pass"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.query.count(), 0)

    def test_report_timestamp_is_generated_per_insert(self):
        self.assertEqual(self.bootstrap().exit_code, 0)
        author = User.query.one()
        first = Report(category="Waste", description="First", location="Here", author=author)
        db.session.add(first)
        db.session.commit()
        time.sleep(0.01)
        second = Report(category="Waste", description="Second", location="Here", author=author)
        db.session.add(second)
        db.session.commit()
        self.assertGreater(second.date_posted, first.date_posted)

    def test_picture_upload_creates_missing_directory(self):
        # Keep temporary files inside the repository rather than system /tmp.
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            picture = io.BytesIO()
            Image.new("RGB", (400, 400)).save(picture, format="PNG")
            picture.seek(0)
            upload = FileStorage(stream=picture, filename="test.png")
            directory = Path(temporary) / "new" / "uploads"
            filename = save_picture(upload, str(directory))
            with Image.open(directory / filename) as saved:
                self.assertEqual(saved.size, (360, 360))


if __name__ == "__main__":
    unittest.main()
