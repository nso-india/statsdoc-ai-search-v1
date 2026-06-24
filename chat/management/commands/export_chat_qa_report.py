import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection


REPORT_SQL = """
WITH ordered AS (
    SELECT
        m.id,
        m.chat_id,
        m.role,
        m.content,
        m.created_at,
        LEAD(m.role) OVER (
            PARTITION BY m.chat_id ORDER BY m.created_at, m.id
        ) AS next_role,
        LEAD(m.content) OVER (
            PARTITION BY m.chat_id ORDER BY m.created_at, m.id
        ) AS answer,
        LEAD(m.created_at) OVER (
            PARTITION BY m.chat_id ORDER BY m.created_at, m.id
        ) AS answer_at
    FROM chat_message m
)
SELECT
    u.email,
    u.username,
    COALESCE(kb.name, '') AS knowledge_base,
    c.title AS chat_title,
    c.id AS chat_id,
    o.content AS question,
    o.created_at AS question_at,
    CASE WHEN o.next_role = 'assistant' THEN o.answer ELSE '' END AS answer,
    CASE WHEN o.next_role = 'assistant' THEN o.answer_at END AS answer_at
FROM ordered o
JOIN chat_chat c ON c.id = o.chat_id
JOIN auth_user u ON u.id = c.user_id
LEFT JOIN uploader_knowledgebase kb ON kb.id = c.knowledge_base_id
WHERE o.role = 'user'
  {date_filter}
ORDER BY o.created_at ASC;
"""


class Command(BaseCommand):
    help = (
        "Export all user questions and assistant answers to CSV "
        "(user email, knowledge base, question, answer, timestamps)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            default="",
            help="Output CSV path (default: chat_qa_report_YYYYMMDD_HHMMSS.csv)",
        )
        parser.add_argument(
            "--from-date",
            dest="from_date",
            default="",
            help="Include questions on/after this date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--to-date",
            dest="to_date",
            default="",
            help="Include questions before this date (YYYY-MM-DD, exclusive)",
        )

    def handle(self, *args, **options):
        date_clauses = []
        params = []

        if options["from_date"]:
            date_clauses.append("AND o.created_at >= %s")
            params.append(options["from_date"])

        if options["to_date"]:
            date_clauses.append("AND o.created_at < %s")
            params.append(options["to_date"])

        sql = REPORT_SQL.format(date_filter="\n  ".join(date_clauses))

        output_path = options["output"] or (
            f"chat_qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        output_path = Path(output_path)

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(columns)
            writer.writerows(rows)

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {len(rows)} question rows to {output_path.resolve()}"
            )
        )
