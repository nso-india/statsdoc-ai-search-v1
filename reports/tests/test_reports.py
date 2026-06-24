from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from chat.models import Chat, Message
from feedback.models import Feedback, ResponseFeedback
from uploader.models import KnowledgeBase, UploadedFile


class AdminReportsAPITestCase(TestCase):
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
        self.kb = KnowledgeBase.objects.create(name="Test KB")
        self.chat = Chat.objects.create(user=self.user, title="Test chat", knowledge_base=self.kb)
        Feedback.objects.create(
            name="Test User",
            email="test@example.com",
            subject="Test subject",
            message="Test message",
            page_url="https://statsdoc.ai.mospi.gov.in/c/1",
        )
        assistant_message = Message.objects.create(
            chat=self.chat,
            role="assistant",
            content='{"response":"Hello","qdrant_data":[]}',
        )
        ResponseFeedback.objects.create(
            user=self.user,
            chat=self.chat,
            message=assistant_message,
            rating="down",
            category="wrong_document",
            details="Wrong source cited",
            user_question="What is GDP?",
            assistant_response="Hello",
        )
        UploadedFile.objects.create(
            file=SimpleUploadedFile("failed.pdf", b"pdf"),
            file_name="failed.pdf",
            status="FAILED",
            knowledge_base=self.kb,
            other_info={"error": "Parse failed"},
        )

    def test_catalog_requires_staff(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/reports/catalog/")
        self.assertEqual(response.status_code, 403)

    def test_catalog_lists_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/catalog/")
        self.assertEqual(response.status_code, 200)
        slugs = {item["slug"] for item in response.data["reports"]}
        self.assertIn("chat_activity", slugs)
        self.assertIn("failed_uploads", slugs)
        self.assertIn("negative_feedback", slugs)

    def test_chat_activity_report(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/chat_activity/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_kb_usage_report(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/kb_usage/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["name"], "Test KB")

    def test_failed_uploads_report(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/failed_uploads/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["error"], "Parse failed")

    def test_citation_accuracy_report(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/citation_accuracy/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_export_all_returns_xlsx(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/export/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"PK"))

    def test_export_single_report(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/user_list/export/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_list_report_", response["Content-Disposition"])

    def test_report_meta_includes_catalog(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/meta/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("reports", response.data)
        self.assertIn("form_statuses", response.data)

    def test_invalid_date_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/chat_activity/?from_date=bad-date")
        self.assertEqual(response.status_code, 400)

    def test_form_feedback_single_export(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/reports/form_feedback/export/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"PK"))
