from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from .constants import FEEDBACK_STATUSES, RESPONSE_FEEDBACK_RATINGS
from .models import Feedback, ResponseFeedback


def _parse_date(value, *, end_of_day=False):
    if not value:
        return None
    dt = datetime.strptime(value, "%Y-%m-%d")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def filter_feedback_queryset(queryset, params):
    from_date = _parse_date(params.get("from_date"))
    to_date = _parse_date(params.get("to_date"), end_of_day=True)
    if from_date:
        queryset = queryset.filter(created_at__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__lte=to_date)

    status = (params.get("status") or "").strip()
    if status:
        queryset = queryset.filter(status=status)

    category = (params.get("category") or "").strip()
    if category:
        queryset = queryset.filter(category=category)

    search = (params.get("q") or "").strip()
    if search:
        queryset = queryset.filter(
            Q(subject__icontains=search)
            | Q(message__icontains=search)
            | Q(email__icontains=search)
            | Q(name__icontains=search)
        )

    return queryset.order_by("-created_at")


def filter_response_feedback_queryset(queryset, params):
    from_date = _parse_date(params.get("from_date"))
    to_date = _parse_date(params.get("to_date"), end_of_day=True)
    if from_date:
        queryset = queryset.filter(created_at__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__lte=to_date)

    rating = (params.get("rating") or "").strip()
    if rating:
        queryset = queryset.filter(rating=rating)

    category = (params.get("category") or "").strip()
    if category:
        queryset = queryset.filter(category=category)

    chat_id = (params.get("chat_id") or "").strip()
    if chat_id:
        queryset = queryset.filter(chat_id=chat_id)

    search = (params.get("q") or "").strip()
    if search:
        queryset = queryset.filter(
            Q(user_question__icontains=search)
            | Q(assistant_response__icontains=search)
            | Q(details__icontains=search)
            | Q(user__email__icontains=search)
            | Q(user__username__icontains=search)
        )

    return queryset.order_by("-created_at")


def get_feedback_list_queryset(params):
    queryset = Feedback.objects.select_related("user").prefetch_related("attachments")
    return filter_feedback_queryset(queryset, params)


def get_response_feedback_list_queryset(params):
    queryset = ResponseFeedback.objects.select_related("user", "message", "chat")
    return filter_response_feedback_queryset(queryset, params)


def paginate_queryset(queryset, params, default_page_size=25, max_page_size=100):
    try:
        page = max(int(params.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(params.get("page_size", default_page_size)), 1), max_page_size)
    except (TypeError, ValueError):
        page_size = default_page_size

    count = queryset.count()
    offset = (page - 1) * page_size
    return {
        "count": count,
        "page": page,
        "page_size": page_size,
        "results": queryset[offset : offset + page_size],
    }


def get_status_choices():
    return [{"value": value, "label": label} for value, label in FEEDBACK_STATUSES]


def get_rating_choices():
    return [{"value": value, "label": label} for value, label in RESPONSE_FEEDBACK_RATINGS]
