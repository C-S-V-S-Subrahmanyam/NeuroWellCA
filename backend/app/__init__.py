from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
import logging

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name='development'):
    """Application factory pattern"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    migrate.init_app(app, db)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register blueprints
    from app.routes import auth_routes, assessment_routes, chat_routes, dashboard_routes
    
    app.register_blueprint(auth_routes.bp, url_prefix='/api/auth')
    app.register_blueprint(assessment_routes.bp, url_prefix='/api/assessments')
    app.register_blueprint(chat_routes.bp, url_prefix='/api/chat')
    app.register_blueprint(dashboard_routes.bp, url_prefix='/api/dashboard')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'NeuroWell-CA Backend'}, 200
    
    # Root endpoint
    @app.route('/')
    def index():
        return {
            'message': 'NeuroWell-CA API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'assessments': '/api/assessments',
                'chat': '/api/chat',
                'dashboard': '/api/dashboard'
            }
        }, 200
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
