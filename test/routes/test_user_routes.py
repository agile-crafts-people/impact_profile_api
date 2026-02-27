"""
Unit tests for User routes.

These tests validate the Flask route layer for the User domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.user_routes import create_user_routes


class TestUserRoutes(unittest.TestCase):
    """Test cases for User routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_user_routes(),
            url_prefix="/api/user",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.user_routes.create_flask_token")
    @patch("src.routes.user_routes.create_flask_breadcrumb")
    @patch("src.routes.user_routes.UserService.create_user")
    @patch("src.routes.user_routes.UserService.get_user")
    def test_create_user_success(
        self,
        mock_get_user,
        mock_create_user,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/user for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_user.return_value = "123"
        mock_get_user.return_value = {
            "_id": "123",
            "name": "test-user",
            "status": "active",
        }

        response = self.client.post(
            "/api/user",
            json={"name": "test-user", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_user.assert_called_once()
        mock_get_user.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.user_routes.create_flask_token")
    @patch("src.routes.user_routes.create_flask_breadcrumb")
    @patch("src.routes.user_routes.UserService.get_users")
    def test_get_users_no_filter(
        self,
        mock_get_users,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/user without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_users.return_value = {
            "items": [
                {"_id": "123", "name": "user1"},
                {"_id": "456", "name": "user2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/user")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_users.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.user_routes.create_flask_token")
    @patch("src.routes.user_routes.create_flask_breadcrumb")
    @patch("src.routes.user_routes.UserService.get_users")
    def test_get_users_with_name_filter(
        self,
        mock_get_users,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/user with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_users.return_value = {
            "items": [{"_id": "123", "name": "test-user"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/user?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_users.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.user_routes.create_flask_token")
    @patch("src.routes.user_routes.create_flask_breadcrumb")
    @patch("src.routes.user_routes.UserService.get_user")
    def test_get_user_success(
        self,
        mock_get_user,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/user/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_user.return_value = {
            "_id": "123",
            "name": "user1",
        }

        response = self.client.get("/api/user/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_user.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.user_routes.create_flask_token")
    @patch("src.routes.user_routes.create_flask_breadcrumb")
    @patch("src.routes.user_routes.UserService.get_user")
    def test_get_user_not_found(
        self,
        mock_get_user,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/user/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_user.side_effect = HTTPNotFound(
            "User 999 not found"
        )

        response = self.client.get("/api/user/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "User 999 not found")

    @patch("src.routes.user_routes.create_flask_token")
    def test_create_user_unauthorized(self, mock_create_token):
        """Test POST /api/user when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/user",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
