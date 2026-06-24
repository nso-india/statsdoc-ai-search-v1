from django.core.management.base import BaseCommand

from feedback.models import ResponseFeedback
from feedback.mospi_quickreview import (
    record_mospi_quickreview_sync_failure,
    submit_response_feedback_to_mospi_quickreview,
)


class Command(BaseCommand):
    help = "Sync chat thumbs up/down ratings to the MoSPI DI Lab quickreview API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-send all ratings (may update duplicates on central portal).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Maximum number of rows to process (0 = all).",
        )

    def handle(self, *args, **options):
        force = options["force"]
        limit = options["limit"]

        queryset = ResponseFeedback.objects.select_related(
            "message", "chat", "user"
        ).order_by("created_at")
        if not force:
            queryset = queryset.filter(mospi_quickreview_synced_at__isnull=True)
        if limit > 0:
            rows = list(queryset[:limit])
        else:
            rows = list(queryset)

        synced = 0
        failed = 0

        for feedback in rows:
            if force:
                feedback.mospi_quickreview_synced_at = None
                feedback.mospi_quickreview_sync_error = ""
                feedback.save(
                    update_fields=[
                        "mospi_quickreview_synced_at",
                        "mospi_quickreview_sync_error",
                    ]
                )

            result = submit_response_feedback_to_mospi_quickreview(
                feedback, force=force
            )
            if result.success:
                synced += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Synced message_id={feedback.message_id} (feedback {feedback.id})"
                    )
                )
            else:
                failed += 1
                record_mospi_quickreview_sync_failure(feedback, result.error)
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed message_id={feedback.message_id}: {result.error}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. processed={len(rows)}, synced={synced}, failed={failed}"
            )
        )
