# Generated manually for ResponseFeedback model

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0004_language"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("feedback", "0002_feedbackattachment"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResponseFeedback",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "rating",
                    models.CharField(
                        choices=[("up", "Helpful"), ("down", "Not helpful")],
                        max_length=10,
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("incorrect_incomplete", "Incorrect or incomplete"),
                            ("not_what_asked", "Not what I asked for"),
                            ("wrong_document", "Wrong document / source"),
                            ("language_issue", "Language or translation issue"),
                            ("slow_buggy", "Slow or buggy"),
                            ("style_tone", "Style or tone"),
                            ("safety_legal", "Safety or legal concern"),
                            ("other", "Other"),
                        ],
                        default="",
                        max_length=30,
                    ),
                ),
                ("details", models.TextField(blank=True, default="")),
                ("user_question", models.TextField(blank=True, default="")),
                ("assistant_response", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "chat",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response_feedback",
                        to="chat.chat",
                    ),
                ),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response_feedback",
                        to="chat.message",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response_feedback",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Response feedback",
                "verbose_name_plural": "Response feedback",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="responsefeedback",
            constraint=models.UniqueConstraint(
                fields=("user", "message"),
                name="unique_response_feedback_per_user_message",
            ),
        ),
    ]
