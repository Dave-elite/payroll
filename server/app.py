from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import timedelta
from flask_restful import Api
from models import db, TokenBlacklist
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from Resources.auth import UserResource, LoginResource
from Resources.attendance import AttendanceResource, AttendanceSummaryResource
from Resources.department import DepartmentResource
from Resources.bonus import BonusResource

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)


# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Configure database
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# App configurations
app.config.update(
    SQLALCHEMY_DATABASE_URI=database_url or 'sqlite:///employee_management.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'your-secret-key'),  # Always use environment variable in production
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=2),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
    JWT_BLACKLIST_ENABLED=True,
    JWT_BLACKLIST_TOKEN_CHECKS=['access', 'refresh']
)

# Initialize extensions
api = Api(app)
jwt = JWTManager(app)
db.init_app(app)
migrate = Migrate(app, db)

# JWT configuration and error handlers
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return TokenBlacklist.query.filter_by(jti=jti).first() is not None

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'message': 'The token has expired',
        'error': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'message': 'Signature verification failed',
        'error': 'invalid_token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'message': 'Request does not contain an access token',
        'error': 'authorization_required'
    }), 401

@jwt.needs_fresh_token_loader
def token_not_fresh_callback(jwt_header, jwt_payload):
    return jsonify({
        'message': 'The token is not fresh',
        'error': 'fresh_token_required'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'message': 'The token has been revoked',
        'error': 'token_revoked'
    }), 401

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource does not exist'
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad request',
        'message': str(error.description)
    }), 400

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

# Create database tables within application context
def initialize_database():
    with app.app_context():
        db.create_all()

# Register API routes
# Note: Import your resource classes here
# from resources.auth import UserRegistration, UserLogin, UserLogout, TokenRefresh
# from resources.employees import EmployeeResource, EmployeeList
# from resources.departments import DepartmentResource, DepartmentList
# etc...

# Add resources to API
api.add_resource(UserResource, '/register')
api.add_resource(AttendanceResource, '/attendance', '/attendance/<int:id>')
api.add_resource(LoginResource, '/login')
api.add_resource(AttendanceSummaryResource, '/summary_attendance')
api.add_resource(DepartmentResource, '/department', '/department/<int:id>')
api.add_resource(BonusResource, '/bonus', '/bonus/<int:id>')
# api.add_resource(UserLogout, '/logout')
# api.add_resource(TokenRefresh, '/refresh')
# api.add_resource(EmployeeResource, '/employee/<int:employee_id>')
# api.add_resource(EmployeeList, '/employees')
# etc...

if __name__ == '__main__':
    initialize_database()
    app.run(debug=os.environ.get('FLASK_DEBUG', True))