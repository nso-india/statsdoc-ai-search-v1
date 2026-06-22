#!/bin/bash
set -euo pipefail
echo "Running deploy.sh script"
if [ "$DEBUG" = "1" ]; then
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
fi


python manage.py collectstatic --noinput
python manage.py migrate
python manage.py init_config

if [ "$DEBUG" = "1" ]; then
    python -m debugpy --listen 0.0.0.0:5678 -m django runserver 0.0.0.0:8000
else
    # Start Gunicorn
    daphne -b 0.0.0.0 -p 8000 config.asgi:application
fi
