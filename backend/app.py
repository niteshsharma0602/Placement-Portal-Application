from flask import Flask, render_template
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from config import Config
from models import db, User, Role
from routes.auth import init_auth_routes
from routes.admin import init_admin_routes
from routes.company import init_company_routes

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
                password=hash_password('admin123'),                      #creating admin user with the admin role
                fs_uniquifier='admin-unique-id', 
                roles=[admin_role]) 
            db.session.commit()

    init_auth_routes(app,user_datastore)
    init_admin_routes(app)
    init_company_routes(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)