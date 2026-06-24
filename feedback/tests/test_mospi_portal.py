from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from feedback.models import Feedback
from feedback.mospi_portal import format_feedback_for_portal, submit_feedback_to_mospi_portal


class MospiPortalSyncTestCase(TestCase):
    def setUp(self):
        self.feedback = Feedback.objects.create(
            name="Test User",
            email="test@example.com",
            subject="Test subject",
            message="Test message body",
            page_url="https://statsdoc.ai.mospi.gov.in/c/1",
        )

    def test_format_feedback_for_portal(self):
        text = format_feedback_for_portal(self.feedback)
        self.assertIn("Subject: Test subject", text)
        self.assertIn("Message: Test message body", text)
        self.assertIn("Page: https://statsdoc.ai.mospi.gov.in/c/1", text)

    @override_settings(
        MOSPI_PORTAL_ENABLED=True,
        MOSPI_PORTAL_FEEDBACK_URL="https://datainnovation.mospi.gov.in/api/submitFeedback",
        MOSPI_PORTAL_DATA_SOURCE="statsdoc",
    )
    @patch("feedback.mospi_portal.requests.post")
    def test_submit_feedback_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "statusCode": True,
            "response": {"id": 99},
        }
        mock_post.return_value = mock_response

        result = submit_feedback_to_mospi_portal(self.feedback)
        self.assertTrue(result.success)
        self.assertEqual(result.portal_id, 99)

        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.mospi_portal_id, 99)
        self.assertIsNotNone(self.feedback.mospi_portal_synced_at)

        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["data_source"], "statsdoc")
        self.assertEqual(payload["email"], "test@example.com")

    @override_settings(MOSPI_PORTAL_ENABLED=True)
    @patch("feedback.mospi_portal.requests.post")
    def test_submit_skips_already_synced(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": {"id": 1}}
        mock_post.return_value = mock_response

        submit_feedback_to_mospi_portal(self.feedback)
        self.assertEqual(mock_post.call_count, 1)
        mock_post.reset_mock()

        result = submit_feedback_to_mospi_portal(self.feedback)
        self.assertTrue(result.success)
        mock_post.assert_not_called()
