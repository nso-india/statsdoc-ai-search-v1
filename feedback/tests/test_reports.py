from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from chat.models import Chat, Message
from feedback.models import Feedback, ResponseFeedback


class FeedbackReportsAPITestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass12345",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass12345",
        )
        self.client = APIClient()
        self.feedback = Feedback.objects.create(
            name="Test User",
            email="test@example.com",
            subject="Test subject",
            message="Test message",
            page_url="https://statsdoc.ai.mospi.gov.in/c/1",
        )
        chat = Chat.objects.create(user=self.user, title="Test chat")
        assistant_message = Message.objects.create(
            chat=chat,
            role="assistant",
            content='{"response":"Hello","qdrant_data":[]}',
        )
        self.response_feedback = ResponseFeedback.objects.create(
            user=self.user,
            chat=chat,
            message=assistant_message,
            rating="down",
            category="incorrect_incomplete",
            details="Wrong answer",
            user_question="What is GDP?",
            assistant_response="Hello",
        )

    def test_feedback_list_requires_staff(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/feedback/list/")
        self.assertEqual(response.status_code, 403)

    def test_feedback_list_paginated_for_staff(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/feedback/list/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["subject"], "Test subject")

    def test_response_feedback_list_for_staff(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/feedback/response/list/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["user_email"], "user1@example.com")

    def test_feedback_export_returns_xlsx(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/feedback/reports/export/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response["Content-Type"],
        )
        self.assertTrue(response.content.startswith(b"PK"))
        self.assertIn("attachment", response["Content-Disposition"])

    def test_feedback_export_requires_staff(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/feedback/reports/export/")
        self.assertEqual(response.status_code, 403)

    def test_feedback_report_meta(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/feedback/reports/meta/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("form_statuses", response.data)
        self.assertIn("response_ratings", response.data)

    def test_feedback_list_date_filter(self):
        self.client.force_authenticate(user=self.admin)
        today = timezone.now().date().isoformat()
        response = self.client.get(f"/api/feedback/list/?from_date={today}&to_date={today}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
