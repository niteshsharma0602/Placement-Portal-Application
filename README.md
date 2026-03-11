# Placement Portal Application

This is a Flask-based web application for managing placement processes, including user authentication, company management, and scheduling. It uses Celery for background tasks and Redis as a message broker.

##  Quick Start

1. **Activate Python virtual environment**

   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server**

   ```bash
   python backend/app.py
   ```

4. **Start Celery worker**

   ```bash
   celery -A backend.tasks worker --loglevel=info
   ```

5. **Start Celery beat (scheduled tasks)**

   ```bash
   celery -A backend.tasks beat --loglevel=info
   ```

##  Notes

- The app uses MailHog (SMTP) for email testing; run it separately if needed.
- Static assets and templates are under `backend/static/` and `backend/templates/`.
