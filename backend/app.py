from flask import Flask
from flask_security import Security, SQLAlchemyUserDatastore
from config import Config
from models import db, User, Role
from routes.auth import init_auth_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    with app.app_context():

        db.create_all()

        # Always create all roles if they don't exist
        user_datastore.find_or_create_role('admin', description='Administrator')
        user_datastore.find_or_create_role('company', description='Company')
        user_datastore.find_or_create_role('student', description='Student')
        db.session.commit()

        if not User.query.filter_by(email = "admin@123.com").first():       #it will check if the admin user already exists
            admin_role = user_datastore.find_or_create_role('admin')     #create admin role 
            user_datastore.create_user(
                email='admin@123.com', 
                password='admin123',                      #creating admin user with the admin role
                fs_uniquifier='admin-unique-id', 
                roles=[admin_role]) 
            db.session.commit()

    init_auth_routes(app,user_datastore)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)