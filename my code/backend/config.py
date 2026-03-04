"""Application configuration management."""
import os
from datetime import timedelta


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///leadgen.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(',')
    
    # Platform
    MAX_LEADS_PER_CAMPAIGN = int(os.getenv('MAX_LEADS_PER_CAMPAIGN', 10000))
    BOT_THRESHOLD = float(os.getenv('BOT_THRESHOLD', 0.8))
    CLICK_TIMEOUT = int(os.getenv('CLICK_TIMEOUT', 3600))
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
