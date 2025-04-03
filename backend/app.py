from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
import os
from config import config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.marksheet import marksheet_bp
    from routes.prediction import prediction_bp
    from routes.timetable import timetable_bp
    from routes.attendance import attendance_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(marksheet_bp, url_prefix='/api/marksheet')
    app.register_blueprint(prediction_bp, url_prefix='/api/prediction')
    app.register_blueprint(timetable_bp, url_prefix='/api/timetable')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {'status': 'healthy'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)