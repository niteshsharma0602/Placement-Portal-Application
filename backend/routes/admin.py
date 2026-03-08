from flask import request, jsonify
from models import db, User, Student, Company, PlacementDrive, Application

def init_admin_routes(app, cache):

    # Dashboard stats - cached for 30 seconds
    # Short timeout since stats change frequently with new registrations/applications
    @app.route('/api/admin/dashboard', methods=['GET'])
    @cache.cached(timeout=30, key_prefix='admin_dashboard')
    def admin_dashboard():
        total_students = Student.query.count()
        total_companies = Company.query.count()
        total_drives = PlacementDrive.query.count()
        total_applications = Application.query.count()
        return jsonify({
            'total_students': total_students,
            'total_companies': total_companies,
            'total_drives': total_drives,
            'total_applications': total_applications
        }), 200

    # Students list - cached for 60 seconds
    # Cache invalidated when student is blacklisted or deactivated
    @app.route('/api/admin/students', methods=['GET'])
    @cache.cached(timeout=60, key_prefix='admin_students')
    def get_all_students():
        students = Student.query.all()
        result = []
        for student in students:
            user = User.query.get(student.user_id)
            result.append({
                'id': student.id,
                'name': student.name,
                'email': user.email,
                'branch': student.branch,
                'cgpa': student.cgpa,
                'year': student.year,
                'skills': student.skills,
                'is_blacklisted': student.is_blacklisted,
                'active': user.active if user else True
            })
        return jsonify(result), 200

    # Companies list - cached for 60 seconds
    # Cache invalidated when company is approved, rejected, blacklisted or deactivated
    @app.route('/api/admin/companies', methods=['GET'])
    @cache.cached(timeout=60, key_prefix='admin_companies')
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
                'is_blacklisted': company.is_blacklisted,
                'active': User.query.get(company.user_id).active
            })
        return jsonify(result), 200

    # Search - cached per query string and type
    # Manual caching used since query varies dynamically
    @app.route('/api/admin/search', methods=['GET'])
    def admin_search():
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'student')
        
        # unique cache key per search query and type
        cache_key = f'search_{search_type}_{query}'
        cached = cache.get(cache_key)
        if cached:
            return jsonify(cached), 200
        
        if search_type == 'student':
            results = Student.query.filter(Student.name.ilike(f'%{query}%')).all()
            data = [{'id': s.id, 'name': s.name, 'branch': s.branch} for s in results]
        else:
            results = Company.query.filter(Company.name.ilike(f'%{query}%')).all()
            data = [{'id': c.id, 'name': c.name, 'industry': c.industry} for c in results]
        
        # cache result for 30 seconds
        cache.set(cache_key, data, timeout=30)
        return jsonify(data), 200

    # Approve or reject a company
    # Clears companies and dashboard cache on change
    @app.route('/api/admin/company/<int:company_id>/approve', methods=['PUT'])
    def approve_company(company_id):
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'message': 'Company not found'}), 404
        status = request.get_json().get('status')
        if status == 'rejected':
            user = User.query.get(company.user_id)
            db.session.delete(company)
            if user:
                db.session.delete(user)
            db.session.commit()
            cache.delete('admin_companies')
            cache.delete('admin_dashboard')
            return jsonify({'message': 'Company rejected and removed'}), 200
        company.approval_status = status
        db.session.commit()
        cache.delete('admin_companies')
        cache.delete('admin_dashboard')
        return jsonify({'message': f'Company {status} successfully'}), 200

    # Approve or reject a placement drive
    # Clears drives and student drives cache so students see updated list
    @app.route('/api/admin/drive/<int:drive_id>/approve', methods=['PUT'])
    def approve_drive(drive_id):
        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            return jsonify({'message': 'Drive not found'}), 404
        status = request.get_json().get('status')
        drive.status = status
        db.session.commit()
        cache.delete('admin_drives')
        cache.delete('student_drives')
        return jsonify({'message': f'Drive {status} successfully'}), 200

    # Blacklist or unblock a student
    # Clears students cache so admin sees updated status
    @app.route('/api/admin/student/<int:student_id>/blacklist', methods=['PUT'])
    def blacklist_student(student_id):
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404
        student.is_blacklisted = request.get_json().get('is_blacklisted')
        db.session.commit()
        cache.delete('admin_students')
        return jsonify({'message': 'Student status updated'}), 200

    # Blacklist or unblock a company
    # Clears companies cache so admin sees updated status
    @app.route('/api/admin/company/<int:company_id>/blacklist', methods=['PUT'])
    def blacklist_company(company_id):
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'message': 'Company not found'}), 404
        company.is_blacklisted = request.get_json().get('is_blacklisted')
        db.session.commit()
        cache.delete('admin_companies')
        return jsonify({'message': 'Company status updated'}), 200

    # All placement drives - cached for 60 seconds
    # Cache invalidated when drive status changes
    @app.route('/api/admin/drives', methods=['GET'])
    @cache.cached(timeout=60, key_prefix='admin_drives')
    def get_all_drives():
        drives = PlacementDrive.query.all()
        result = []
        for d in drives:
            company = Company.query.get(d.company_id)
            result.append({
                'id': d.id,
                'title': d.title,
                'company_id': d.company_id,
                'company_name': company.name if company else 'N/A',
                'status': d.status,
                'deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else None
            })
        return jsonify(result), 200

    # All applications - not cached since it changes frequently
    @app.route('/api/admin/applications', methods=['GET'])
    def get_all_applications():
        applications = Application.query.all()
        result = []
        for a in applications:
            student = Student.query.get(a.student_id)
            drive = PlacementDrive.query.get(a.drive_id)
            result.append({
                'id': a.id,
                'student_name': student.name if student else 'N/A',
                'drive_title': drive.title if drive else 'N/A',
                'status': a.status,
                'applied_at': a.applied_at.strftime('%Y-%m-%d') if a.applied_at else None
            })
        return jsonify(result), 200

    # Deactivate or activate a student account
    # Clears students cache on change
    @app.route('/api/admin/student/<int:student_id>/deactivate', methods=['PUT'])
    def deactivate_student(student_id):
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404
        user = User.query.get(student.user_id)
        if user:
            user.active = not user.active
        db.session.commit()
        cache.delete('admin_students')
        return jsonify({'message': 'Student account status updated', 'active': user.active}), 200

    # Deactivate or activate a company account
    # Clears companies cache on change
    @app.route('/api/admin/company/<int:company_id>/deactivate', methods=['PUT'])
    def deactivate_company(company_id):
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'message': 'Company not found'}), 404
        user = User.query.get(company.user_id)
        if user:
            user.active = not user.active
        db.session.commit()
        cache.delete('admin_companies')
        return jsonify({'message': 'Company account status updated', 'active': user.active}), 200