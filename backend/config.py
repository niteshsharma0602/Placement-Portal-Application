import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'I-am-vengeance2'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, '..', 'instance', 'placement_portal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = "devil-of-hell's-kitchen"
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_REDIRECT_BEHAVIOR = 'spa'  
    WTF_CSRF_ENABLED = False 
    SESSION_PERMANENT = False
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 60  