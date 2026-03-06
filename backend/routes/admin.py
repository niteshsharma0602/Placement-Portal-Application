from flask import request, jsonify
from flask_security import roles_required
from models import db, User, Student, Company, PlacementDrive, Application

def init_admin_routes(app):

    @app.route('/api/admin/dashboard', methods=['GET'])
    def admin_dashboard():
        total_students = Student.query.count()
        total_companies = Company.query.count()
        total_drives = PlacementDrive.query.count()
        
        return jsonify({
            'total_students': total_students,
            'total_companies': total_companies,
            'total_drives': total_drives
        }), 200
    
    @app.route('/api/admin/students', methods=['GET'])
    def get_all_students():
        students = Student.query.all()
        result = []
        for student in students:  
            result.append({
                'id': student.id,
                'name': student.name,
                'branch': student.branch,
                'cgpa': student.cgpa,
                'year': student.year,
                'skills': student.skills,
                'is_blacklisted': student.is_blacklisted
            })
        return jsonify(result), 200

    @app.route('/api/admin/companies', methods=['GET'])
    def get_all_companies():
        companies = Company.query.all()
        result = []
        for company in companies:
            result.append({
                'id': company.id,
                'name': company.name,
                'industry': company.industry,
                'website': company.website,
                'hr_contact': company.hr_contact,
                'approval_status': company.approval_status,
                'is_blacklisted': company.is_blacklisted
            })
        return jsonify(result), 200
    
    @app.route('/api/admin/search', methods=['GET'])
    def admin_search():
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'student')
        
        if search_type == 'student':
            results = Student.query.filter(Student.name.ilike(f'%{query}%')).all()
            data = [{'id': s.id, 'name': s.name, 'branch': s.branch} for s in results]
        else:
            results = Company.query.filter(Company.name.ilike(f'%{query}%')).all()
            data = [{'id': c.id, 'name': c.name, 'industry': c.industry} for c in results]
        
        return jsonify(data), 200
    
    # Approve or reject a company
    @app.route('/api/admin/company/<int:company_id>/approve', methods=['PUT'])
    def approve_company(company_id):
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'message': 'Company not found'}), 404
        status = request.get_json().get('status')  # 'approved' or 'rejected'
        company.approval_status = status
        db.session.commit()
        return jsonify({'message': f'Company {status} successfully'}), 200

    # Approve or reject a placement drive
    @app.route('/api/admin/drive/<int:drive_id>/approve', methods=['PUT'])
    def approve_drive(drive_id):
        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            return jsonify({'message': 'Drive not found'}), 404
        status = request.get_json().get('status')  # 'approved' or 'rejected'
        drive.status = status
        db.session.commit()
        return jsonify({'message': f'Drive {status} successfully'}), 200

    # Blacklist or activate a student
    @app.route('/api/admin/student/<int:student_id>/blacklist', methods=['PUT'])
    def blacklist_student(student_id):
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404
        student.is_blacklisted = request.get_json().get('is_blacklisted')
        db.session.commit()
        return jsonify({'message': 'Student status updated'}), 200

    # Blacklist or activate a company
    @app.route('/api/admin/company/<int:company_id>/blacklist', methods=['PUT'])
    def blacklist_company(company_id):
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'message': 'Company not found'}), 404
        company.is_blacklisted = request.get_json().get('is_blacklisted')
        db.session.commit()
        return jsonify({'message': 'Company status updated'}), 200

    # View all placement drives
    @app.route('/api/admin/drives', methods=['GET'])
    def get_all_drives():
        drives = PlacementDrive.query.all()
        return jsonify([{
            'id': d.id,
            'title': d.title,
            'company_id': d.company_id,
            'status': d.status,
            'deadline': str(d.deadline)
        } for d in drives]), 200

    # View all applications
    @app.route('/api/admin/applications', methods=['GET'])
    def get_all_applications():
        applications = Application.query.all()
        return jsonify([{
            'id': a.id,
            'student_id': a.student_id,
            'drive_id': a.drive_id,
            'status': a.status,
            'applied_at': str(a.applied_at)
        } for a in applications]), 200