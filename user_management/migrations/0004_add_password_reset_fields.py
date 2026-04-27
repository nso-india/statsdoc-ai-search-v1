from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_management", "0003_rename_password_reset_sent_at_user_account_locked_until_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="password_reset_token",
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="password_reset_sent_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
