from flask import request, jsonify
from models import db, Student, PlacementDrive, Application, Placement,Company
from datetime import datetime

def init_student_routes(app, cache):

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
            'is_blacklisted': student.is_blacklisted,
        }), 200
    
    @app.route('/api/student/profile/update/<int:student_id>', methods=['PUT'])
    def update_student_profile(student_id):
        data = request.get_json()
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404

        student.name = data.get('name', student.name)
        student.branch = data.get('branch', student.branch)
        student.cgpa = data.get('cgpa', student.cgpa)
        student.year = data.get('year', student.year)
        student.skills = data.get('skills', student.skills)
        student.resume = data.get('resume', student.resume)
        db.session.commit()

        return jsonify({'message': 'Profile updated successfully'}), 200

    @app.route('/api/student/drives', methods=['GET'])
    @cache.cached(timeout=60, key_prefix='student_drives')
    def get_approved_drives():
        
        # only fetch drives with status approved
        drives = PlacementDrive.query.filter_by(status='approved').all()

        return jsonify([{
            'id': d.id,
            'company_id': d.company_id,
            'company_name': d.company.name,
            'company_industry': d.company.industry,
            'company_website': d.company.website,
            'company_hr_contact': d.company.hr_contact,
            'title': d.title,
            'description': d.description,
            'eligible_branch': d.eligible_branch,
            'eligible_cgpa': d.eligible_cgpa,
            'eligible_year': d.eligible_year,
            'deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else None,
            'status': d.status,
            'salary': d.salary
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

        # eligibility check if student meets the criteria
        if drive.eligible_cgpa and student.cgpa < drive.eligible_cgpa:
            return jsonify({'message': f'You need minimum CGPA of {drive.eligible_cgpa} to apply'}), 403

        if drive.eligible_branch and drive.eligible_branch.lower() != student.branch.lower():
            return jsonify({'message': f'This drive is only for {drive.eligible_branch} branch'}), 403

        if drive.eligible_year and drive.eligible_year > student.year:
            return jsonify({'message': f'You do not have enough experience required'}), 403

        # create new application
        application = Application(
            student_id=student_id,
            drive_id=drive_id,
            status='applied'   
        )
        db.session.add(application)
        db.session.commit()
        cache.delete('student_drives')

        return jsonify({'message': 'Application submitted successfully'}), 201

    @app.route('/api/student/applications/<int:student_id>', methods=['GET'])
    def get_student_applications(student_id):

        applications = Application.query.filter_by(student_id=student_id).all()

        result = []
        for a in applications:
            drive = PlacementDrive.query.get(a.drive_id)
            company = Company.query.get(drive.company_id) if drive else None
            result.append({
                'id': a.id,
                'drive_id': a.drive_id,
                'drive_title': drive.title if drive else 'N/A',
                'company_name': company.name if company else 'N/A',
                'applied_at': a.applied_at.strftime('%Y-%m-%d') if a.applied_at else None,
                'interview_date': a.interview_date.strftime('%Y-%m-%d') if a.interview_date else None,
                'status': a.status
            })
        return jsonify(result), 200

    @app.route('/api/student/placements/<int:student_id>', methods=['GET'])
    def get_student_placements(student_id):
        placements = Placement.query.filter_by(student_id=student_id).all()
        result = []
        for p in placements:
            company = Company.query.get(p.company_id)
            drive = PlacementDrive.query.get(p.drive_id)
            result.append({
                'id': p.id,
                'company_name': company.name if company else 'N/A',
                'drive_title': drive.title if drive else 'N/A',
                'salary': drive.salary if drive else None,
                'joining_date': p.joining_date.strftime('%Y-%m-%d') if p.joining_date else None,
                'created_at': p.created_at.strftime('%Y-%m-%d') if p.created_at else None
            })
        return jsonify(result), 200
    
    #student gets a csv export of their application history via email
    @app.route('/api/student/export/<int:student_id>', methods=['POST'])
    def trigger_csv_export(student_id):
        from tasks import export_applications_csv

        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404

        # Queue the task — runs asynchronously in Celery worker
        export_applications_csv.delay(student_id)

        return jsonify({'message': 'Export started! You will receive an email when it is ready.'}), 202

