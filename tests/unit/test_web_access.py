import unittest

try:
    import flask  # noqa: F401
    import mysql.connector  # noqa: F401
except ModuleNotFoundError as error:
    raise unittest.SkipTest("Project web dependencies are not installed; run poetry install to enable web access tests.") from error

from source.app import create_app


class TestConfig:
    SECRET_KEY = "unit-test-secret-key"
    TESTING = True
    SESSION_COOKIE_SECURE = False


class WebAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.client.session_transaction() as session:
            session.clear()

    def _login_as(self, role: str):
        with self.client.session_transaction() as session:
            session["user_id"] = 10
            session["username"] = "test-user"
            session["role"] = role

    def test_health_endpoint_is_public(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_reader_cannot_open_admin_account_page(self):
        self._login_as("READER")
        response = self.client.get("/admin/accounts")
        self.assertEqual(response.status_code, 403)

    def test_librarian_cannot_open_admin_account_page(self):
        self._login_as("LIBRARIAN")
        response = self.client.get("/admin/accounts")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_open_admin_account_page(self):
        self._login_as("ADMIN")
        response = self.client.get("/admin/accounts")
        self.assertEqual(response.status_code, 200)

    def test_reader_cannot_open_librarian_book_management_page(self):
        self._login_as("READER")
        response = self.client.get("/librarian/books")
        self.assertEqual(response.status_code, 403)

    def test_librarian_can_open_book_management_page(self):
        self._login_as("LIBRARIAN")
        response = self.client.get("/librarian/books")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
