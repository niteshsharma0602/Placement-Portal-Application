from flask import Flask, render_template, session
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from config import Config
from models import db, User, Role
from routes.auth import init_auth_routes
from routes.admin import init_admin_routes
from routes.company import init_company_routes
from routes.student import init_student_routes
import uuid
from datetime import datetime
from flask_caching import Cache

cache = Cache()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    cache.init_app(app)
    
    # Generate a unique app session version to invalidate old sessions on restart
    app.session_version = str(uuid.uuid4())
    app.session_start_time = datetime.now().isoformat()
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    with app.app_context():

        db.create_all()

        user_datastore.find_or_create_role('admin', description='Administrator')
        user_datastore.find_or_create_role('company', description='Company')
        user_datastore.find_or_create_role('student', description='Student')
        db.session.commit()

        if not User.query.filter_by(email = "admin@123.com").first():       
            admin_role = user_datastore.find_or_create_role('admin')    
            user_datastore.create_user(
                email='admin@123.com', 
                password=hash_password('admin123'),                      
                fs_uniquifier='admin-unique-id', 
                roles=[admin_role]) 
            db.session.commit()

    init_auth_routes(app, user_datastore, app.session_version)
    init_admin_routes(app, cache)
    init_company_routes(app)
    init_student_routes(app, cache)

    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.before_request
    def make_session_non_permanent():
        session.permanent = False

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)