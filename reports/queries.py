from datetime import datetime

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from chat.models import Chat
from feedback.constants import (
    RESPONSE_CATEGORY_LANGUAGE,
    RESPONSE_CATEGORY_WRONG_DOC,
    RATING_DOWN,
)
from feedback.models import ResponseFeedback
from feedback.query_utils import (
    get_feedback_list_queryset,
    get_response_feedback_list_queryset,
    paginate_queryset,
)
from uploader.constants import COMPLETED, FAILED
from uploader.models import KnowledgeBase, UploadedFile

User = get_user_model()

REPORT_CATALOG = [
    {
        "slug": "form_feedback",
        "name": "Form Feedback Report",
        "phase": 1,
        "category": "Feedback",
        "description": "Sidebar feedback form submissions",
    },
    {
        "slug": "response_feedback",
        "name": "Response Feedback Report",
        "phase": 1,
        "category": "Feedback",
        "description": "Chat thumbs up/down ratings",
    },
    {
        "slug": "chat_activity",
        "name": "Chat Activity Report",
        "phase": 2,
        "category": "Usage & Analytics",
        "description": "Daily chat volume and active users",
    },
    {
        "slug": "kb_usage",
        "name": "Knowledge Base Usage Report",
        "phase": 2,
        "category": "Usage & Analytics",
        "description": "Knowledge base usage by chats and files",
    },
    {
        "slug": "user_activity",
        "name": "User Activity Report",
        "phase": 2,
        "category": "Usage & Analytics",
        "description": "Chats per user in selected period",
    },
    {
        "slug": "document_uploads",
        "name": "Document Upload Report",
        "phase": 2,
        "category": "Usage & Analytics",
        "description": "All uploaded documents with status",
    },
    {
        "slug": "failed_uploads",
        "name": "Failed Upload Report",
        "phase": 2,
        "category": "Usage & Analytics",
        "description": "Failed document uploads with error details",
    },
    {
        "slug": "user_list",
        "name": "User List Export",
        "phase": 3,
        "category": "Admin & Security",
        "description": "All registered users with roles and status",
    },
    {
        "slug": "admin_audit_log",
        "name": "Admin Audit Log",
        "phase": 3,
        "category": "Admin & Security",
        "description": "Django admin actions log",
    },
    {
        "slug": "login_activity",
        "name": "Login Activity Report",
        "phase": 3,
        "category": "Admin & Security",
        "description": "User last login and account status",
    },
    {
        "slug": "negative_feedback",
        "name": "Negative Feedback Analysis",
        "phase": 4,
        "category": "AI Quality",
        "description": "Thumbs down breakdown by reason",
    },
    {
        "slug": "citation_accuracy",
        "name": "Citation Accuracy Report",
        "phase": 4,
        "category": "AI Quality",
        "description": "Wrong document/source complaints",
    },
    {
        "slug": "language_issues",
        "name": "Language Issue Report",
        "phase": 4,
        "category": "AI Quality",
        "description": "Language and translation feedback",
    },
]


def _parse_date(value, *, end_of_day=False):
    if not value:
        return None
    dt = datetime.strptime(value, "%Y-%m-%d")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def _date_range(params):
    return (
        _parse_date(params.get("from_date")),
        _parse_date(params.get("to_date"), end_of_day=True),
    )


def _apply_created_filter(queryset, params, field="created_at"):
    from_date, to_date = _date_range(params)
    if from_date:
        queryset = queryset.filter(**{f"{field}__gte": from_date})
    if to_date:
        queryset = queryset.filter(**{f"{field}__lte": to_date})
    return queryset


def get_report_slug(slug):
    for item in REPORT_CATALOG:
        if item["slug"] == slug:
            return item
    return None


def query_chat_activity(params):
    queryset = Chat.objects.all()
    queryset = _apply_created_filter(queryset, params)
    daily = (
        queryset.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(chat_count=Count("id"), active_users=Count("user_id", distinct=True))
        .order_by("date")
    )
    rows = [
        {
            "date": item["date"].isoformat() if item["date"] else "",
            "chat_count": item["chat_count"],
            "active_users": item["active_users"],
        }
        for item in daily
    ]
    return rows, len(rows)


def query_kb_usage(params):
    queryset = KnowledgeBase.objects.annotate(
        chat_count=Count("chats", distinct=True),
        file_count=Count("files", distinct=True),
        completed_files=Count("files", filter=Q(files__status=COMPLETED), distinct=True),
        failed_files=Count("files", filter=Q(files__status=FAILED), distinct=True),
    ).order_by("-chat_count", "name")
    rows = [
        {
            "id": kb.id,
            "name": kb.name,
            "chat_count": kb.chat_count,
            "file_count": kb.file_count,
            "completed_files": kb.completed_files,
            "failed_files": kb.failed_files,
            "created_at": kb.created_at.isoformat(),
        }
        for kb in queryset
    ]
    return rows, len(rows)


def query_user_activity(params):
    queryset = Chat.objects.select_related("user")
    queryset = _apply_created_filter(queryset, params)
    aggregated = (
        queryset.values("user_id", "user__email", "user__username")
        .annotate(chat_count=Count("id"))
        .order_by("-chat_count")
    )
    rows = [
        {
            "user_id": item["user_id"],
            "email": item["user__email"] or "",
            "username": item["user__username"] or "",
            "chat_count": item["chat_count"],
        }
        for item in aggregated
    ]
    return rows, len(rows)


def query_document_uploads(params):
    queryset = UploadedFile.objects.select_related("knowledge_base", "chat")
    queryset = _apply_created_filter(queryset, params, field="uploaded_at")
    rows = [
        {
            "id": item.id,
            "file_name": item.file_name,
            "status": item.status,
            "knowledge_base": item.knowledge_base.name if item.knowledge_base_id else "",
            "knowledge_base_id": item.knowledge_base_id,
            "chat_id": item.chat_id,
            "uploaded_at": item.uploaded_at.isoformat(),
        }
        for item in queryset.order_by("-uploaded_at")
    ]
    return rows, len(rows)


def query_failed_uploads(params):
    queryset = UploadedFile.objects.filter(status=FAILED).select_related("knowledge_base")
    queryset = _apply_created_filter(queryset, params, field="uploaded_at")
    rows = []
    for item in queryset.order_by("-uploaded_at"):
        other_info = item.other_info or {}
        rows.append(
            {
                "id": item.id,
                "file_name": item.file_name,
                "knowledge_base": item.knowledge_base.name if item.knowledge_base_id else "",
                "error": other_info.get("error") or other_info.get("message") or "",
                "technical_error": other_info.get("technical_error") or "",
                "uploaded_at": item.uploaded_at.isoformat(),
            }
        )
    return rows, len(rows)


def query_user_list(params):
    queryset = User.objects.all().order_by("-date_joined")
    rows = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "last_login": user.last_login.isoformat() if user.last_login else "",
            "date_joined": user.date_joined.isoformat() if user.date_joined else "",
        }
        for user in queryset
    ]
    return rows, len(rows)


def query_admin_audit_log(params):
    queryset = LogEntry.objects.select_related("user", "content_type")
    queryset = _apply_created_filter(queryset, params, field="action_time")
    total_count = queryset.count()
    rows = [
        {
            "id": entry.id,
            "action_time": entry.action_time.isoformat(),
            "user": entry.user.username if entry.user_id else "",
            "action": entry.get_action_flag_display(),
            "object_repr": entry.object_repr,
            "change_message": entry.change_message,
        }
        for entry in queryset.order_by("-action_time")[:5000]
    ]
    return rows, total_count


def query_login_activity(params):
    queryset = User.objects.all().order_by("-last_login", "-date_joined")
    rows = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "last_login": user.last_login.isoformat() if user.last_login else "",
            "date_joined": user.date_joined.isoformat() if user.date_joined else "",
            "days_since_login": (
                (timezone.now() - user.last_login).days if user.last_login else ""
            ),
        }
        for user in queryset
    ]
    return rows, len(rows)


def query_negative_feedback(params):
    queryset = get_response_feedback_list_queryset({**params, "rating": RATING_DOWN})
    total_count = queryset.count()
    summary = (
        queryset.values("category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    category_labels = dict(ResponseFeedback._meta.get_field("category").choices)
    breakdown = [
        {
            "category": item["category"] or "unspecified",
            "category_label": category_labels.get(item["category"], item["category"] or "Unspecified"),
            "count": item["count"],
        }
        for item in summary
    ]
    details = [
        {
            "id": str(item.id),
            "user_email": item.user.email if item.user_id else "",
            "chat_id": item.chat_id,
            "category": item.category,
            "category_label": category_labels.get(item.category, item.category),
            "details": item.details,
            "user_question": item.user_question[:500],
            "created_at": item.created_at.isoformat(),
        }
        for item in queryset[:500]
    ]
    return {"breakdown": breakdown, "details": details}, total_count


def query_citation_accuracy(params):
    queryset = get_response_feedback_list_queryset(
        {**params, "category": RESPONSE_CATEGORY_WRONG_DOC}
    )
    rows = [
        {
            "id": str(item.id),
            "user_email": item.user.email if item.user_id else "",
            "chat_id": item.chat_id,
            "details": item.details,
            "user_question": item.user_question,
            "assistant_response": item.assistant_response[:500],
            "created_at": item.created_at.isoformat(),
        }
        for item in queryset[:5000]
    ]
    return rows, queryset.count()


def query_language_issues(params):
    queryset = get_response_feedback_list_queryset(
        {**params, "category": RESPONSE_CATEGORY_LANGUAGE}
    )
    rows = [
        {
            "id": str(item.id),
            "user_email": item.user.email if item.user_id else "",
            "chat_id": item.chat_id,
            "details": item.details,
            "user_question": item.user_question,
            "assistant_response": item.assistant_response[:500],
            "created_at": item.created_at.isoformat(),
        }
        for item in queryset[:5000]
    ]
    return rows, queryset.count()


def query_form_feedback(params):
    queryset = get_feedback_list_queryset(params)
    return paginate_queryset(queryset, params)


def query_response_feedback(params):
    queryset = get_response_feedback_list_queryset(params)
    return paginate_queryset(queryset, params)


def _list_result(query_fn, params):
    rows, count = query_fn(params)
    return {"results": rows, "count": count}


def _negative_result(params):
    data, count = query_negative_feedback(params)
    return {**data, "count": count}


def run_report_query(slug, params):
    handlers = {
        "form_feedback": query_form_feedback,
        "response_feedback": query_response_feedback,
        "chat_activity": lambda p: _list_result(query_chat_activity, p),
        "kb_usage": lambda p: _list_result(query_kb_usage, p),
        "user_activity": lambda p: _list_result(query_user_activity, p),
        "document_uploads": lambda p: _list_result(query_document_uploads, p),
        "failed_uploads": lambda p: _list_result(query_failed_uploads, p),
        "user_list": lambda p: _list_result(query_user_list, p),
        "admin_audit_log": lambda p: _list_result(query_admin_audit_log, p),
        "login_activity": lambda p: _list_result(query_login_activity, p),
        "negative_feedback": _negative_result,
        "citation_accuracy": lambda p: _list_result(query_citation_accuracy, p),
        "language_issues": lambda p: _list_result(query_language_issues, p),
    }
    return handlers.get(slug)
