from flask import Blueprint, request, jsonify
from flask_security import SQLAlchemyUserDatastore
from models import db, User, Role, Student, Company
import uuid

def init_auth_routes(app,user_datastore):

    @app.route('/api/register/student' , methods = ['POST'])
    def register_student():
        data = request.get_json()

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        student_role = user_datastore.find_role('student')
        new_user = user_datastore.create_user(
            email=data['email'],
            password=data['password'],
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
            password=data['password'],
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
        
        # Check if user exists and password is correct
        if not user or not user.verify_and_update_password(data['password']):
            return jsonify({'message': 'Invalid email or password'}), 401
        
        # Check if user is active
        if not user.active:
            return jsonify({'message': 'Account is deactivated'}), 403
        
        role = user.roles[0].name if user.roles else None
        
        return jsonify({
            'message': 'Login successful',
            'role': role,
            'user_id': user.id,
            'email': user.email
        }), 200


    # Logout
    @app.route('/api/logout', methods=['POST'])
    def logout():
        return jsonify({'message': 'Logged out successfully'}), 200

