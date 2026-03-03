import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'I-am-vengeance'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///placement_portal.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = "devil-of-hell's-kitchen"
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False