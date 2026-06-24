from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from chat.models import Chat, Message
from django.contrib.auth import get_user_model

from feedback.models import ResponseFeedback
from feedback.mospi_quickreview import (
    build_quickreview_payload,
    submit_response_feedback_to_mospi_quickreview,
)


class MospiQuickreviewSyncTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass12345",
        )
        self.chat = Chat.objects.create(user=self.user, title="Test chat")
        self.message = Message.objects.create(
            chat=self.chat,
            role="assistant",
            content='{"content":"Hello"}',
        )
        self.feedback = ResponseFeedback.objects.create(
            user=self.user,
            chat=self.chat,
            message=self.message,
            rating="up",
            user_question="What is GDP?",
            assistant_response="Hello",
        )

    def test_build_quickreview_payload(self):
        payload = build_quickreview_payload(self.feedback)
        self.assertEqual(payload["message_id"], str(self.message.id))
        self.assertEqual(payload["session_id"], str(self.chat.id))
        self.assertEqual(payload["rating"], "up")
        self.assertEqual(payload["prompt"], "What is GDP?")
        self.assertEqual(payload["product"], "statsdoc")
        self.assertEqual(payload["category"], "")
        self.assertEqual(payload["details"], "")

    @override_settings(
        MOSPI_PORTAL_ENABLED=True,
        MOSPI_QUICKREVIEW_URL="https://datainnovation.mospi.gov.in/api/quickreview",
        MOSPI_PORTAL_PRODUCT="statsdoc",
    )
    @patch("feedback.mospi_quickreview.requests.post")
    def test_submit_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = submit_response_feedback_to_mospi_quickreview(self.feedback)
        self.assertTrue(result.success)

        self.feedback.refresh_from_db()
        self.assertIsNotNone(self.feedback.mospi_quickreview_synced_at)

        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["product"], "statsdoc")
        self.assertEqual(payload["message_id"], str(self.message.id))

    @override_settings(MOSPI_PORTAL_ENABLED=True)
    @patch("feedback.mospi_quickreview.requests.post")
    def test_submit_skips_already_synced(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        submit_response_feedback_to_mospi_quickreview(self.feedback)
        mock_post.reset_mock()

        result = submit_response_feedback_to_mospi_quickreview(self.feedback)
        self.assertTrue(result.success)
        mock_post.assert_not_called()

    @override_settings(MOSPI_PORTAL_ENABLED=True)
    @patch("feedback.mospi_quickreview.requests.post")
    def test_force_resyncs(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        submit_response_feedback_to_mospi_quickreview(self.feedback)
        mock_post.reset_mock()

        result = submit_response_feedback_to_mospi_quickreview(self.feedback, force=True)
        self.assertTrue(result.success)
        mock_post.assert_called_once()
