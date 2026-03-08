from flask import request, jsonify
from models import db, Student, PlacementDrive, Application, Placement
from datetime import datetime

def init_student_routes(app):

    @app.route('/api/student/profile/<int:user_id>', methods=['GET'])
    def get_student_profile(user_id):

        student = Student.query.filter_by(user_id=user_id).first()

        if not student:
            return jsonify({'message': 'Student not found'}), 404

        return jsonify({
            'id': student.id,
            'user_id': student.user_id,
            'name': student.name,
            'branch': student.branch,
            'cgpa': student.cgpa,
            'year': student.year,
            'skills': student.skills,
            'resume': student.resume,
            'is_blacklisted': student.is_blacklisted
        }), 200

    @app.route('/api/student/drives', methods=['GET'])
    def get_approved_drives():

        # only fetch drives with status approved
        drives = PlacementDrive.query.filter_by(status='approved').all()

        return jsonify([{
            'id': d.id,
            'company_id': d.company_id,
            'title': d.title,
            'description': d.description,
            'eligible_branch': d.eligible_branch,
            'eligible_cgpa': d.eligible_cgpa,
            'eligible_year': d.eligible_year,
            'deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else None,
            'status': d.status
        } for d in drives]), 200

    @app.route('/api/student/apply', methods=['POST'])
    def apply_drive():

        data = request.get_json()
        student_id = data.get('student_id')
        drive_id = data.get('drive_id')

        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404

        if student.is_blacklisted:
            return jsonify({'message': 'You are blacklisted and cannot apply'}), 403

        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            return jsonify({'message': 'Drive not found'}), 404

        if drive.status != 'approved':
            return jsonify({'message': 'This drive is not open for applications'}), 403

        # check if student already applied to this drive
        existing = Application.query.filter_by(
            student_id=student_id,
            drive_id=drive_id
        ).first()
        if existing:
            return jsonify({'message': 'You have already applied to this drive'}), 400

        # create new application
        application = Application(
            student_id=student_id,
            drive_id=drive_id,
            status='applied'   
        )
        db.session.add(application)
        db.session.commit()

        return jsonify({'message': 'Application submitted successfully'}), 201

    @app.route('/api/student/applications/<int:student_id>', methods=['GET'])
    def get_student_applications(student_id):

        applications = Application.query.filter_by(student_id=student_id).all()

        return jsonify([{
            'id': a.id,
            'drive_id': a.drive_id,
            'applied_at': a.applied_at.strftime('%Y-%m-%d') if a.applied_at else None,
            'interview_date': a.interview_date.strftime('%Y-%m-%d') if a.interview_date else None,
            'status': a.status
        } for a in applications]), 200

    @app.route('/api/student/placements/<int:student_id>', methods=['GET'])
    def get_student_placements(student_id):
        placements = Placement.query.filter_by(student_id=student_id).all()
        return jsonify([{
            'id': p.id,
            'company_id': p.company_id,
            'drive_id': p.drive_id,
            'salary': p.salary,
            'joining_date': p.joining_date.strftime('%Y-%m-%d') if p.joining_date else None,
            'created_at': p.created_at.strftime('%Y-%m-%d') if p.created_at else None
        } for p in placements]), 200
    
    # ─────────────────────────────────────────
    # TRIGGER CSV EXPORT (Async via Celery)
    # Student clicks Export button → Celery job runs
    # in background → student gets email when done
    # ─────────────────────────────────────────
    @app.route('/api/student/export/<int:student_id>', methods=['POST'])
    def trigger_csv_export(student_id):
        from tasks import export_applications_csv

        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404

        # Queue the task — runs asynchronously in Celery worker
        export_applications_csv.delay(student_id)

        return jsonify({'message': 'Export started! You will receive an email when it is ready.'}), 202

