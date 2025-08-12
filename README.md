# 🚀 Django Project Setup Guide

## *1 Setup Virtual Environment*
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build and start containers
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop containers
docker-compose down

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver

# swagger document
http://127.0.0.1:8000/swagger/
