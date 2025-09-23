#!/bin/bash

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Making migrations ==="
python manage.py makemigrations

echo "=== Applying migrations ==="
python manage.py migrate

echo "=== Creating superuser ==="
echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@heritageacademy.com', 'admin123');
    print('Superuser created successfully!');
else:
    print('Superuser already exists!');
" | python manage.py shell

echo "=== Build completed ==="
