from celery import Celery
from celery.schedules import crontab
from flask_mail import Mail, Message
from datetime import datetime, timezone, timedelta
import csv
import os

IST = timezone(timedelta(hours=5, minutes=30))

celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)


celery.conf.beat_schedule = {

    'daily-deadline-reminder': {
        'task': 'tasks.send_deadline_reminder',
        'schedule': crontab(hour=8, minute=0),
    },

    'monthly-placement-report': {
        'task': 'tasks.send_monthly_report',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),
    },
}

celery.conf.timezone = 'Asia/Kolkata'

def get_flask_app():

    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__)) 

    from app import create_app

    app = create_app()

    app.config['MAIL_SERVER'] = 'localhost'
    app.config['MAIL_PORT'] = 1025
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_DEFAULT_SENDER'] = 'noreply@placementportal.com'

    mail = Mail(app)
    return app, mail


@celery.task(name='tasks.send_deadline_reminder')
def send_deadline_reminder():
    app, mail = get_flask_app()
    with app.app_context():
        from models import Student, PlacementDrive, Application, User
        from datetime import datetime, timedelta, timezone
        
        IST = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(IST)
        upcoming = now + timedelta(days=2)
        
        drives = PlacementDrive.query.filter(
            PlacementDrive.status == 'approved',
            PlacementDrive.deadline >= now,
            PlacementDrive.deadline <= upcoming
        ).all()
        
        count = 0
        for drive in drives:
            applied_student_ids = [a.student_id for a in drive.applications]
            students = Student.query.filter(
                Student.is_blacklisted == False
            ).all()
            
            for student in students:
                if student.id not in applied_student_ids:
                    user = User.query.get(student.user_id)
                    if user:
                        msg = Message(
                            subject=f'Deadline Reminder: {drive.title}',
                            sender='noreply@placementportal.com',
                            recipients=[user.email]
                        )
                        msg.body = f'''Hi {student.name},

This is a reminder that the application deadline for {drive.title} is approaching.

Deadline: {drive.deadline.strftime('%Y-%m-%d')}

Login to the Placement Portal to apply before the deadline.

Placement Portal Team'''
                        mail.send(msg)
                        count += 1
        
        print(f'[Reminder] Deadline reminders sent: {count}')


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


@celery.task(name='tasks.export_applications_csv')
def export_applications_csv(student_id):
    app, mail = get_flask_app()

    with app.app_context():
        from models import Application, Student, PlacementDrive, Company, User

        student = Student.query.get(student_id)

        user = User.query.get(student.user_id)
        applications = Application.query.filter_by(student_id=student_id).all()

        export_dir = os.path.join(os.path.dirname(__file__), 'static', 'exports')
        os.makedirs(export_dir, exist_ok=True)

        filename = f'applications_student_{student_id}.csv'
        filepath = os.path.join(export_dir, filename)

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


@celery.task(name='tasks.export_company_csv')
def export_company_csv(company_id):
    app, mail = get_flask_app()
    with app.app_context():
        from models import Company, PlacementDrive, Application, Student, User
        import csv, os

        company = Company.query.get(company_id)
        if not company:
            return

        drives = PlacementDrive.query.filter_by(company_id=company_id).all()
        drive_ids = [d.id for d in drives]
        applications = Application.query.filter(Application.drive_id.in_(drive_ids)).all()

        export_dir = os.path.join(os.path.dirname(__file__), 'static', 'exports') 
        os.makedirs(export_dir, exist_ok=True)
        filename = f'company_{company_id}_applications.csv'
        filepath = os.path.join(export_dir, filename)

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Student Name', 'Drive Title', 'Applied At', 'Interview Date', 'Status'])
            for a in applications:
                student = Student.query.get(a.student_id)
                drive = PlacementDrive.query.get(a.drive_id)
                writer.writerow([
                    student.name if student else 'N/A',
                    drive.title if drive else 'N/A',
                    a.applied_at.strftime('%Y-%m-%d') if a.applied_at else '',
                    a.interview_date.strftime('%Y-%m-%d') if a.interview_date else '',
                    a.status
                ])

        user = User.query.get(company.user_id)
        if user:
            msg = Message(
                subject='Your Applications Export is Ready',
                sender='noreply@placementportal.com',
                recipients=[user.email]
            )
            msg.body = f'''Hi {company.name},

Your applications export is ready. Download it from:
http://localhost:5000/static/exports/{filename}

Placement Portal Team'''
            mail.send(msg)