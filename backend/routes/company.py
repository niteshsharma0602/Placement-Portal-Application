from flask import request, jsonify
from models import db, Company, PlacementDrive, Application, Placement, Student ,User
from datetime import datetime

def init_company_routes(app):

    @app.route('/api/company/profile/<int:user_id>', methods=['GET'])
    def get_company_profile(user_id):
        company = Company.query.filter_by(user_id=user_id).first()

        if not company:
            return jsonify({'message': 'Company not found'}), 404
        
        return jsonify({
            'id': company.id,
            'user_id': company.user_id,
            'name': company.name,
            'industry': company.industry,
            'website': company.website,
            'hr_contact': company.hr_contact,
            'approval_status': company.approval_status,
            'is_blacklisted': company.is_blacklisted
        }), 200

    @app.route('/api/company/drives/<int:company_id>', methods=['GET'])
    def get_company_drives(company_id):
        drives = PlacementDrive.query.filter_by(company_id=company_id).all()
        return jsonify([{
            'id': d.id,
            'title': d.title,
            'description': d.description,
            'eligible_branch': d.eligible_branch,
            'eligible_cgpa': d.eligible_cgpa,
            'experience': d.experience,
            'deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else None,
            'status': d.status,
            'applicant_count': len(d.applications),
            'salary': d.salary
        } for d in drives]), 200

    @app.route('/api/company/drive/create', methods=['POST'])
    def create_drive():
        data = request.get_json()
        company = Company.query.get(data.get('company_id'))
        if not company:
            return jsonify({'message': 'Company not found'}), 404
        
        if company.approval_status != 'approved':
            return jsonify({'message': 'Your company is not approved yet'}), 403
        
        if company.is_blacklisted:
            return jsonify({'message': 'Your company is blacklisted'}), 403

        drive = PlacementDrive(
            company_id=data['company_id'],
            title=data['title'],
            description=data.get('description'),
            eligible_branch=data.get('eligible_branch'),
            eligible_cgpa=data.get('eligible_cgpa'),
            experience=data.get('experience'),
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d').date() if data.get('deadline') else None,
            status='pending',
            salary=data.get('salary')
        )
        db.session.add(drive)
        db.session.commit()
        return jsonify({'message': 'Drive created! Waiting for admin approval'}), 201
    
    @app.route('/api/company/drive/<int:drive_id>/close', methods=['PUT'])
    def close_drive(drive_id):
        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            return jsonify({'message': 'Drive not found'}), 404
        
        drive.status = 'closed'
        db.session.commit()
        return jsonify({'message': 'Drive closed successfully'}), 200


    @app.route('/api/company/applications/<int:company_id>', methods=['GET'])
    def get_company_applications(company_id):
        drives = PlacementDrive.query.filter_by(company_id=company_id).all()
        drive_ids = [d.id for d in drives]
        applications = Application.query.filter(Application.drive_id.in_(drive_ids)).all()
        result = []

        for a in applications:
            student = Student.query.get(a.student_id)
            drive = PlacementDrive.query.get(a.drive_id)
            user = User.query.get(student.user_id) if student else None
            result.append({
                'id': a.id,
                'student_id': a.student_id,
                'student_name': student.name if student else 'N/A',
                'student_email': user.email if user else 'N/A',
                'student_branch': student.branch if student else 'N/A',
                'student_cgpa': student.cgpa if student else 'N/A',
                'drive_id': a.drive_id,
                'drive_title': drive.title if drive else 'N/A',
                'applied_at': a.applied_at.strftime('%Y-%m-%d') if a.applied_at else None,
                'interview_date': a.interview_date.strftime('%Y-%m-%d') if a.interview_date else None,
                'status': a.status,
                'student_resume': student.resume if student else 'N/A',
            })
        return jsonify(result), 200


    @app.route('/api/company/application/<int:app_id>/status', methods=['PUT'])
    def update_application_status(app_id):
        data = request.get_json()

        application = Application.query.get(app_id)
        if not application:
            return jsonify({'message': 'Application not found'}), 404

        new_status = data['status']
        application.status = new_status

        if new_status == 'interview' and data.get('interview_date'):
            application.interview_date = datetime.strptime(data['interview_date'], '%Y-%m-%d')

        if new_status == 'selected':
            existing_placement = Placement.query.filter_by(
                student_id=application.student_id,
                drive_id=application.drive_id
            ).first()

            if not existing_placement:
                drive = PlacementDrive.query.get(application.drive_id)
                placement = Placement(
                    student_id=application.student_id,
                    company_id=drive.company_id,
                    drive_id=application.drive_id,
                    salary=drive.salary
                )
                db.session.add(placement)

        db.session.commit()
        return jsonify({'message': f'Application marked as {new_status}'}), 200

    @app.route('/api/company/placements/<int:company_id>', methods=['GET'])
    def get_company_placements(company_id):
        placements = Placement.query.filter_by(company_id=company_id).all()
        result = []

        for p in placements:
            student = Student.query.get(p.student_id)
            drive = PlacementDrive.query.get(p.drive_id)
            user = User.query.get(student.user_id) if student else None
            result.append({
                'id': p.id,
                'student_name': student.name if student else 'N/A',
                'student_email': user.email if user else 'N/A',
                'drive_title': drive.title if drive else 'N/A',
                'salary': drive.salary if drive else None,
            })
        return jsonify(result), 200

    @app.route('/api/company/export/<int:company_id>', methods=['POST'])
    def trigger_company_export(company_id):
        from tasks import export_company_csv
        company = Company.query.get(company_id)

        if not company:
            return jsonify({'message': 'Company not found'}), 404
        
        export_company_csv.delay(company_id)
        return jsonify({'message': 'Export started! You will receive an email when ready.'}), 202