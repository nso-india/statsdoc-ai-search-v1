CATEGORY_BUG = "bug"
CATEGORY_FEATURE = "feature"
CATEGORY_GENERAL = "general"
CATEGORY_DATA = "data"

FEEDBACK_CATEGORIES = (
    (CATEGORY_BUG, "Bug / Issue"),
    (CATEGORY_FEATURE, "Feature Request"),
    (CATEGORY_GENERAL, "General"),
    (CATEGORY_DATA, "Data / Content"),
)

STATUS_NEW = "new"
STATUS_IN_REVIEW = "in_review"
STATUS_RESOLVED = "resolved"

FEEDBACK_STATUSES = (
    (STATUS_NEW, "New"),
    (STATUS_IN_REVIEW, "In Review"),
    (STATUS_RESOLVED, "Resolved"),
)

# Optional screenshot attachments on feedback submissions
MAX_FEEDBACK_ATTACHMENTS = 3
MAX_FEEDBACK_ATTACHMENT_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB per file

ALLOWED_FEEDBACK_ATTACHMENT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_FEEDBACK_ATTACHMENT_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}

# Per-answer feedback (thumbs up/down on chat responses)
RATING_UP = "up"
RATING_DOWN = "down"

RESPONSE_FEEDBACK_RATINGS = (
    (RATING_UP, "Helpful"),
    (RATING_DOWN, "Not helpful"),
)

RESPONSE_CATEGORY_INCORRECT = "incorrect_incomplete"
RESPONSE_CATEGORY_NOT_ASKED = "not_what_asked"
RESPONSE_CATEGORY_WRONG_DOC = "wrong_document"
RESPONSE_CATEGORY_LANGUAGE = "language_issue"
RESPONSE_CATEGORY_SLOW = "slow_buggy"
RESPONSE_CATEGORY_STYLE = "style_tone"
RESPONSE_CATEGORY_SAFETY = "safety_legal"
RESPONSE_CATEGORY_OTHER = "other"

RESPONSE_FEEDBACK_CATEGORIES = (
    (RESPONSE_CATEGORY_INCORRECT, "Incorrect or incomplete"),
    (RESPONSE_CATEGORY_NOT_ASKED, "Not what I asked for"),
    (RESPONSE_CATEGORY_WRONG_DOC, "Wrong document / source"),
    (RESPONSE_CATEGORY_LANGUAGE, "Language or translation issue"),
    (RESPONSE_CATEGORY_SLOW, "Slow or buggy"),
    (RESPONSE_CATEGORY_STYLE, "Style or tone"),
    (RESPONSE_CATEGORY_SAFETY, "Safety or legal concern"),
    (RESPONSE_CATEGORY_OTHER, "Other"),
)

RESPONSE_FEEDBACK_CATEGORY_VALUES = {choice[0] for choice in RESPONSE_FEEDBACK_CATEGORIES}
MAX_RESPONSE_FEEDBACK_DETAILS_LENGTH = 2000
