"""
Unit tests for Platform routes.

These tests validate the Flask route layer for the Platform domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.platform_routes import create_platform_routes


class TestPlatformRoutes(unittest.TestCase):
    """Test cases for Platform routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_platform_routes(),
            url_prefix="/api/platform",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.platform_routes.create_flask_token")
    @patch("src.routes.platform_routes.create_flask_breadcrumb")
    @patch("src.routes.platform_routes.PlatformService.create_platform")
    @patch("src.routes.platform_routes.PlatformService.get_platform")
    def test_create_platform_success(
        self,
        mock_get_platform,
        mock_create_platform,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/platform for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_platform.return_value = "123"
        mock_get_platform.return_value = {
            "_id": "123",
            "name": "test-platform",
            "status": "active",
        }

        response = self.client.post(
            "/api/platform",
            json={"name": "test-platform", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_platform.assert_called_once()
        mock_get_platform.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.platform_routes.create_flask_token")
    @patch("src.routes.platform_routes.create_flask_breadcrumb")
    @patch("src.routes.platform_routes.PlatformService.get_platforms")
    def test_get_platforms_no_filter(
        self,
        mock_get_platforms,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/platform without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_platforms.return_value = {
            "items": [
                {"_id": "123", "name": "platform1"},
                {"_id": "456", "name": "platform2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/platform")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_platforms.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.platform_routes.create_flask_token")
    @patch("src.routes.platform_routes.create_flask_breadcrumb")
    @patch("src.routes.platform_routes.PlatformService.get_platforms")
    def test_get_platforms_with_name_filter(
        self,
        mock_get_platforms,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/platform with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_platforms.return_value = {
            "items": [{"_id": "123", "name": "test-platform"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/platform?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_platforms.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.platform_routes.create_flask_token")
    @patch("src.routes.platform_routes.create_flask_breadcrumb")
    @patch("src.routes.platform_routes.PlatformService.get_platform")
    def test_get_platform_success(
        self,
        mock_get_platform,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/platform/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_platform.return_value = {
            "_id": "123",
            "name": "platform1",
        }

        response = self.client.get("/api/platform/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_platform.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.platform_routes.create_flask_token")
    @patch("src.routes.platform_routes.create_flask_breadcrumb")
    @patch("src.routes.platform_routes.PlatformService.get_platform")
    def test_get_platform_not_found(
        self,
        mock_get_platform,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/platform/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_platform.side_effect = HTTPNotFound(
            "Platform 999 not found"
        )

        response = self.client.get("/api/platform/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Platform 999 not found")

    @patch("src.routes.platform_routes.create_flask_token")
    def test_create_platform_unauthorized(self, mock_create_token):
        """Test POST /api/platform when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/platform",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
