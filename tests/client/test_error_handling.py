import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root and modern_client to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../modern_client')))

from modern_client.services.api import ApiService
import httpx

class TestApiServiceErrorHandling(unittest.TestCase):
    def setUp(self):
        self.api_service = ApiService()
        self.mock_handler = MagicMock()
        self.api_service.set_error_handler(self.mock_handler)

    @patch('httpx.Client.get')
    def test_get_products_error(self, mock_get):
        # Simulate an HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=mock_response)
        mock_get.return_value = mock_response

        # Call the method
        result = self.api_service.get_products()

        # Verify result is empty list (default fallback)
        self.assertEqual(result, [])

        # Verify handler was called
        self.assertTrue(self.mock_handler.called)
        args, _ = self.mock_handler.call_args
        self.assertIn("Fetch products failed", args[0])
        self.assertIn("404 Not Found", args[0])

    @patch('httpx.Client.post')
    def test_login_error(self, mock_post):
        # Simulate an HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("401 Unauthorized", request=MagicMock(), response=mock_response)
        mock_post.return_value = mock_response

        # Call the method
        result = self.api_service.login("user", "pass")

        # Verify result is None
        self.assertIsNone(result)

        # Verify handler was called
        self.assertTrue(self.mock_handler.called)
        args, _ = self.mock_handler.call_args
        self.assertIn("Login failed", args[0])

if __name__ == '__main__':
    unittest.main()
