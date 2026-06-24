from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("feedback", "0003_responsefeedback"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedback",
            name="mospi_portal_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="feedback",
            name="mospi_portal_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="feedback",
            name="mospi_portal_sync_error",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
