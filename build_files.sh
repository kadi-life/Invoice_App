#!/bin/bash

# Create staticfiles directory if it doesn't exist
mkdir -p staticfiles

# Install project dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput