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