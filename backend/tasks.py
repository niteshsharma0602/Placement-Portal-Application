from celery import Celery
from celery.schedules import crontab
from flask_mail import Mail, Message
from datetime import datetime, timezone, timedelta
import csv
import os


IST = timezone(timedelta(hours=5, minutes=30))

#celery setup

celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Defines when scheduled jobs run automatically

celery.conf.beat_schedule = {

    # Job 1: runs every day at 8:00 AM
    'daily-interview-reminder': {
        'task': 'tasks.send_interview_reminders',
        'schedule': crontab(hour=8, minute=0),
    },

    # Job 2: runs on the 1st of every month at 9:00 AM
    'monthly-placement-report': {
        'task': 'tasks.send_monthly_report',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),
    },
}

celery.conf.timezone = 'Asia/Kolkata'

def get_flask_app():

    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))  # adds backend/ to path

    from app import create_app

    app = create_app()

    # Mail config — points to MailHog running on port 1025
    app.config['MAIL_SERVER'] = 'localhost'
    app.config['MAIL_PORT'] = 1025
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_DEFAULT_SENDER'] = 'noreply@placementportal.com'

    mail = Mail(app)
    return app, mail



# Finds all students with interviews scheduled in the next 2 days and sends them a reminder email
@celery.task(name='tasks.send_interview_reminders')
def send_interview_reminders():
    app, mail = get_flask_app()

    with app.app_context():
        from models import Application, Student, PlacementDrive, User

        today = datetime.now(IST).date()
        reminder_window = today + timedelta(days=2)

        applications = Application.query.filter(
            Application.status == 'interview',
            Application.interview_date != None
        ).all()

        sent_count = 0
        for app_record in applications:
            if not app_record.interview_date:
                continue

            interview_date = app_record.interview_date.date() if hasattr(app_record.interview_date, 'date') else app_record.interview_date

            if today <= interview_date <= reminder_window:
                student = Student.query.get(app_record.student_id)
                user = User.query.get(student.user_id)
                drive = PlacementDrive.query.get(app_record.drive_id)

                msg = Message(
                    subject='Interview Reminder — Placement Portal',
                    recipients=[user.email],
                    body=f"""
Dear {student.name},

This is a reminder that you have an interview scheduled.

Drive: {drive.title}
Interview Date: {interview_date}

Please be prepared and report on time.

Best regards,
Placement Portal Team
                    """.strip()
                )

                mail.send(msg)
                sent_count += 1
                print(f'[Reminder] Sent to {user.email} for drive: {drive.title}')

        print(f'[Reminder] Total reminders sent: {sent_count}')
        return f'Sent {sent_count} reminders'


# Generates an HTML report of the past month's placement activity and emails it to admin
@celery.task(name='tasks.send_monthly_report')
def send_monthly_report():
    app, mail = get_flask_app()

    with app.app_context():
        from models import PlacementDrive, Application, User

        now = datetime.now(IST)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_drives = PlacementDrive.query.filter(
            PlacementDrive.created_at >= month_start
        ).count()

        total_applications = Application.query.filter(
            Application.applied_at >= month_start
        ).count()

        total_selected = Application.query.filter(
            Application.applied_at >= month_start,
            Application.status == 'selected'
        ).count()

        total_rejected = Application.query.filter(
            Application.applied_at >= month_start,
            Application.status == 'rejected'
        ).count()

        # HTML email
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Monthly Placement Report — {now.strftime('%B %Y')}</h2>
            <p>Here is the placement activity summary for this month:</p>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
                <tr style="background:#f0f0f0"><th>Metric</th><th>Count</th></tr>
                <tr><td>New Placement Drives</td><td>{total_drives}</td></tr>
                <tr><td>Total Applications</td><td>{total_applications}</td></tr>
                <tr><td>Students Selected</td><td>{total_selected}</td></tr>
                <tr><td>Students Rejected</td><td>{total_rejected}</td></tr>
            </table>
            <br>
            <p>Generated on: {now.strftime('%d %B %Y at %H:%M')}</p>
            <p>— Placement Portal System</p>
        </body>
        </html>
        """

        # Send to admin
        admin_user = User.query.filter(
            User.roles.any(name='admin')
        ).first()

        if admin_user:
            msg = Message(
                subject=f'Monthly Placement Report — {now.strftime("%B %Y")}',
                recipients=[admin_user.email],
                html=html_body
            )
            mail.send(msg)
            print(f'[Monthly Report] Sent to {admin_user.email}')
            return f'Report sent to {admin_user.email}'
        else:
            print('[Monthly Report] No admin found')
            return 'No admin found'



# Student export their application history to a CSV file and sends them an email alert when done
@celery.task(name='tasks.export_applications_csv')
def export_applications_csv(student_id):
    app, mail = get_flask_app()

    with app.app_context():
        from models import Application, Student, PlacementDrive, Company, User

        student = Student.query.get(student_id)

        user = User.query.get(student.user_id)
        applications = Application.query.filter_by(student_id=student_id).all()

        # Create exports directory if it doesn't exist
        export_dir = os.path.join(os.path.dirname(__file__), 'static', 'exports')
        os.makedirs(export_dir, exist_ok=True)

        filename = f'applications_student_{student_id}.csv'
        filepath = os.path.join(export_dir, filename)

        # Write CSV
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Application ID', 'Student ID', 'Drive Title', 'Company Name', 'Applied At', 'Interview Date', 'Status'])

            for a in applications:
                drive = PlacementDrive.query.get(a.drive_id)
                company = Company.query.get(drive.company_id) if drive else None
                writer.writerow([
                    a.id,
                    student_id,
                    drive.title if drive else 'N/A',
                    company.name if company else 'N/A',
                    a.applied_at.strftime('%Y-%m-%d') if a.applied_at else '',
                    a.interview_date.strftime('%Y-%m-%d') if a.interview_date else '',
                    a.status
                ])

        # Send email alert to student
        msg = Message(
            subject='Your Application Export is Ready — Placement Portal',
            recipients=[user.email],
            body=f"""
Dear {student.name},

Your application history CSV export is ready.

You can download it from:
http://localhost:5000/static/exports/{filename}

Best regards,
Placement Portal Team
            """.strip()
        )
        mail.send(msg)

        print(f'[CSV Export] Export ready for student {student_id}: {filename}')
        return f'CSV exported: {filename}'