#!/bin/bash
# Exit on error
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Making migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate

echo "Build completed successfully!"

# Make script executable (this won't run on Vercel but is useful for local testing)
chmod +x build_files.sh