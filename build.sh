#!/bin/bash
set -o errexit  # Exit on any error

echo "=== Environment Information ==="
python --version
pip --version
echo "Python path: $(which python)"
echo "Pip path: $(which pip)"

echo "=== Upgrading pip ==="
python -m pip install --upgrade pip

echo "=== Installing dependencies with verbose output ==="
pip install -r requirements.txt --verbose --no-cache-dir

echo "=== Verifying critical package installations ==="
python -c "import django; print(f'✓ Django {django.get_version()} installed successfully')" || {
    echo "❌ Django installation failed"
    echo "Attempting to install Django directly..."
    pip install "Django==4.2.16" --no-cache-dir
    python -c "import django; print(f'✓ Django {django.get_version()} installed successfully')"
}

python -c "import gunicorn; print('✓ Gunicorn installed successfully')" || {
    echo "❌ Gunicorn installation failed"
    echo "Attempting to install Gunicorn directly..."
    pip install "gunicorn==21.2.0" --no-cache-dir
    python -c "import gunicorn; print('✓ Gunicorn installed successfully')"
}

echo "=== Listing installed packages ==="
pip list | grep -E "(Django|gunicorn|whitenoise)"

echo "=== Finding Django project ==="
if [ ! -d "./school_mgmt" ]; then
    echo "❌ Error: school_mgmt directory not found!"
    echo "Available directories:"
    ls -la
    exit 1
fi

echo "✓ Found Django project in: ./school_mgmt"
cd school_mgmt

echo "=== Testing Django installation ==="
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_mgmt.settings')
import django
django.setup()
print('✓ Django setup successful')
"

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Making migrations ==="
python manage.py makemigrations --no-input

echo "=== Applying migrations ==="
python manage.py migrate --no-input

echo "=== Running system checks ==="
python manage.py check --deploy

echo "=== Creating superuser (optional) ==="
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@heritageacademy.com', 'admin123')
    print('✓ Superuser created successfully')
else:
    print('✓ Superuser already exists')
EOF

echo "=== Build completed successfully ==="
echo "✓ All dependencies installed"
echo "✓ Django project configured"
echo "✓ Database migrations applied"
echo "✓ Static files collected"