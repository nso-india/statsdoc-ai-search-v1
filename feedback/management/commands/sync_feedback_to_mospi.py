from django.core.management.base import BaseCommand

from feedback.models import Feedback
from feedback.mospi_portal import record_mospi_portal_sync_failure, submit_feedback_to_mospi_portal


class Command(BaseCommand):
    help = "Sync form feedback submissions to the MoSPI DI Lab central portal."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-send all feedback rows (may create duplicates on central portal).",
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

        queryset = Feedback.objects.prefetch_related("attachments").order_by("created_at")
        if not force:
            queryset = queryset.filter(mospi_portal_synced_at__isnull=True)
        if limit > 0:
            feedback_rows = list(queryset[:limit])
        else:
            feedback_rows = list(queryset)

        synced = 0
        failed = 0

        for feedback in feedback_rows:
            if force:
                feedback.mospi_portal_synced_at = None
                feedback.mospi_portal_id = None
                feedback.mospi_portal_sync_error = ""
                feedback.save(
                    update_fields=[
                        "mospi_portal_synced_at",
                        "mospi_portal_id",
                        "mospi_portal_sync_error",
                    ]
                )

            result = submit_feedback_to_mospi_portal(feedback, force=force)
            if result.success:
                synced += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Synced {feedback.id} -> portal id {result.portal_id}"
                    )
                )
            else:
                failed += 1
                record_mospi_portal_sync_failure(feedback, result.error)
                self.stdout.write(
                    self.style.ERROR(f"Failed {feedback.id}: {result.error}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. processed={len(feedback_rows)}, synced={synced}, failed={failed}"
            )
        )
