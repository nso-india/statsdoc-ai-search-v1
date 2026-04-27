#!/bin/bash
set -euo pipefail
echo "Running deploy-celery.sh script"
if [ "$DEBUG" = "1" ]; then
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
fi


python manage.py collectstatic --noinput
# Removed: python manage.py migrate - Only web container should run migrations

if [ "$DEBUG" = "1" ]; then
    echo "Running in debug mode"
    watchmedo auto-restart --directory=./ --pattern="*.py" --recursive -- \
    python -m debugpy --listen 0.0.0.0:5678 -m celery -A config worker --loglevel=info --pool=solo
else
    celery -A config worker --loglevel=info
fi
