from flask import Blueprint, request, jsonify, session
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from models import db, User, Role, Student, Company
import uuid

def init_auth_routes(app, user_datastore, session_version):

    @app.route('/api/register/student' , methods = ['POST'])
    def register_student():
        data = request.get_json()

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        student_role = user_datastore.find_role('student')
        new_user = user_datastore.create_user(
            email=data['email'],
            password=hash_password(data['password']),
            fs_uniquifier=str(uuid.uuid4()),
            roles=[student_role]
        )

        db.session.commit()

        new_student = Student(
            user_id=new_user.id,
            name=data['name'],
            branch=data.get('branch'),
            cgpa=data.get('cgpa'),
            year=data.get('year'),
            skills=data.get('skills')
        )
        db.session.add(new_student)
        db.session.commit()

        return jsonify({'message': 'Student registered successfully'}), 201
    
    @app.route('/api/register/company', methods=['POST'])
    def register_company():
        data = request.get_json()
        
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        # Create user with company role
        company_role = user_datastore.find_role('company')
        new_user = user_datastore.create_user(
            email=data['email'],
            password=hash_password(data['password']),
            fs_uniquifier=str(uuid.uuid4()),
            roles=[company_role]
        )
        
        db.session.commit()

        # Create company profile
        new_company = Company(
            user_id=new_user.id,
            name=data['name'],
            industry=data.get('industry'),
            website=data.get('website'),
            hr_contact=data.get('hr_contact'),
            approval_status='pending'
        )
        db.session.add(new_company)
        db.session.commit()
        
        return jsonify({'message': 'Company registered successfully, waiting for admin approval'}), 201

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.verify_and_update_password(data['password']):
            return jsonify({'message': 'Invalid email or password'}), 401
        if not user.active:
            return jsonify({'message': 'Account is deactivated'}), 403
        
        role = user.roles[0].name if user.roles else None
        
        # set flask session
        session['user_id'] = user.id
        session['role'] = role
        session['email'] = user.email
        session['version'] = session_version  # Track session version to invalidate on app restart

        return jsonify({
            'message': 'Login successful',
            'role': role,
            'user_id': user.id,
            'email': user.email
        }), 200


    @app.route('/api/verify', methods=['GET'])
    def verify():
        # Check if session exists and version matches current app version
        if 'user_id' in session:
            # Invalidate session if version doesn't match (app was restarted)
            if session.get('version') != session_version:
                session.clear()
                return jsonify({'valid': False}), 401
            
            return jsonify({
                'valid': True,
                'user_id': session['user_id'],
                'role': session['role'],
                'email': session['email']
            }), 200
        return jsonify({'valid': False}), 401

    @app.route('/api/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify({'message': 'Logged out successfully'}), 200
