from datetime import datetime


def validate_date_params(params):
    """Return an error message if from_date/to_date are invalid."""
    for key in ("from_date", "to_date"):
        value = (params.get(key) or "").strip()
        if not value:
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return f"Invalid {key}. Use YYYY-MM-DD format."
    from_date = (params.get("from_date") or "").strip()
    to_date = (params.get("to_date") or "").strip()
    if from_date and to_date and from_date > to_date:
        return "from_date cannot be after to_date."
    return None
