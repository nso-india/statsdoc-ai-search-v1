from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("feedback", "0004_feedback_mospi_portal_sync"),
    ]

    operations = [
        migrations.AddField(
            model_name="responsefeedback",
            name="mospi_quickreview_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="responsefeedback",
            name="mospi_quickreview_sync_error",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
