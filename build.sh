#!/usr/bin/env bash
# Runs on every Render deploy.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Creates your admin account the first time (uses the DJANGO_SUPERUSER_* variables).
# If it already exists this just says so and carries on.
python manage.py createsuperuser --no-input || echo "Admin account already exists, skipping."
