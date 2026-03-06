from flask import request, jsonify
from models import db, Company, PlacementDrive, Application
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
            'eligible_year': d.eligible_year,
            'deadline': str(d.deadline) if d.deadline else None,
            'status': d.status 
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
            eligible_year=data.get('eligible_year'),
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d') if data.get('deadline') else None,
            status='pending' 
        )

        db.session.add(drive)
        db.session.commit()

        return jsonify({'message': 'Drive created! Waiting for admin approval'}), 201

    @app.route('/api/company/applications/<int:company_id>', methods=['GET'])
    def get_company_applications(company_id):

        drives = PlacementDrive.query.filter_by(company_id=company_id).all()

        drive_ids = [d.id for d in drives]

        applications = Application.query.filter(Application.drive_id.in_(drive_ids)).all()

        return jsonify([{
            'id': a.id,
            'student_id': a.student_id,
            'drive_id': a.drive_id,
            'applied_at': str(a.applied_at) if a.applied_at else None,
            'interview_date': str(a.interview_date) if a.interview_date else None,
            'status': a.status  
        } for a in applications]), 200

    @app.route('/api/company/application/<int:app_id>/status', methods=['PUT'])
    def update_application_status(app_id):

        data = request.get_json()

        application = Application.query.get(app_id)

        if not application:
            return jsonify({'message': 'Application not found'}), 404

        application.status = data['status']
        db.session.commit()

        return jsonify({'message': f'Application marked as {data["status"]}'}), 200