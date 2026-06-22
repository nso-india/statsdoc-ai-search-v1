import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from feedback.models import Feedback


class Command(BaseCommand):
    help = (
        "Export feedback submissions to CSV "
        "(name, email, subject, message, status, timestamps)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            default="",
            help="Output CSV path (default: feedback_report_YYYYMMDD_HHMMSS.csv)",
        )
        parser.add_argument(
            "--from-date",
            dest="from_date",
            default="",
            help="Include submissions on/after this date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--to-date",
            dest="to_date",
            default="",
            help="Include submissions before this date (YYYY-MM-DD, exclusive)",
        )
        parser.add_argument(
            "--status",
            default="",
            help="Filter by status: new, in_review, resolved",
        )

    def handle(self, *args, **options):
        queryset = Feedback.objects.select_related("user").prefetch_related(
            "attachments"
        ).order_by("created_at")

        if options["from_date"]:
            from_dt = timezone.make_aware(
                datetime.strptime(options["from_date"], "%Y-%m-%d")
            )
            queryset = queryset.filter(created_at__gte=from_dt)

        if options["to_date"]:
            to_dt = timezone.make_aware(
                datetime.strptime(options["to_date"], "%Y-%m-%d")
            )
            queryset = queryset.filter(created_at__lt=to_dt)

        if options["status"]:
            queryset = queryset.filter(status=options["status"])

        output_path = options["output"] or (
            f"feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        output_path = Path(output_path)

        columns = [
            "id",
            "name",
            "email",
            "user_email",
            "category",
            "subject",
            "message",
            "page_url",
            "status",
            "attachment_count",
            "attachment_urls",
            "attachment_filenames",
            "created_at",
            "updated_at",
        ]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        row_count = 0
        with output_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(columns)
            for feedback in queryset:
                attachment_urls = []
                attachment_names = []
                for attachment in feedback.attachments.all():
                    attachment_urls.append(attachment.file.url)
                    attachment_names.append(attachment.original_filename)

                writer.writerow(
                    [
                        feedback.id,
                        feedback.name,
                        feedback.email,
                        feedback.user.email if feedback.user_id else "",
                        feedback.category,
                        feedback.subject,
                        feedback.message,
                        feedback.page_url,
                        feedback.status,
                        len(attachment_urls),
                        " | ".join(attachment_urls),
                        " | ".join(attachment_names),
                        feedback.created_at.isoformat(),
                        feedback.updated_at.isoformat(),
                    ]
                )
                row_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {row_count} feedback row(s) to {output_path.resolve()}"
            )
        )
