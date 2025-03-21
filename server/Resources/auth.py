from flask_restful import Resource, reqparse
from flask import request
from models import db, User, Employee, Department
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import generate_password_hash, check_password_hash
import re
from datetime import datetime

class UserResource(Resource):
    """
    User resource for handling user related operations with enhanced role management.
    """
    parser = reqparse.RequestParser()
    parser.add_argument('first_name', type=str, required=True, help='first name is required ')
    parser.add_argument('last_name', type=str, required=True, help='last name is required ')
    parser.add_argument('date_of_birth', type=str, required=True, help='Date of Birth is required')
    parser.add_argument('phone', type=str, required=True, help='Phone number is required')
    parser.add_argument('email', type=str, required=True, help='Email is required')
    parser.add_argument('gender', type=str, required=True, help='Gender is required')
    parser.add_argument('address', type=str, required=True, help='Address is required')
    parser.add_argument('hire_date', type=str, required=True, help='Hire Date is required')
    parser.add_argument('position', type=str, required=True, help='Position is required')
    parser.add_argument('salary', type=float, required=True, help='Salary is required', default=0.00)
    parser.add_argument('password', type=str, required=True, help='Password is required')
    parser.add_argument('confirm_password', type=str, required=True, help='Confirm password is required')
    parser.add_argument('department_id', type=int, required=False, help='Department ID for managers')
    parser.add_argument('role', type=str, required=False, help='Optional user role specification')

    def post(self):
        data = self.parser.parse_args()

        # Validate the email format 
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return {"message": "Invalid email address"}, 400

        # Check phone number and email uniqueness in Employee table
        if Employee.query.filter_by(phone=data['phone']).first():
            return {"message": "Phone number already exists"}, 422
        if Employee.query.filter_by(email=data['email']).first():
            return {"message": "Email address already exists"}, 422

        # Validate password matching
        if data['password'] != data['confirm_password']:
            return {'message': "Passwords do not match"}, 422
        
        # Hash the password
        hashed_password = generate_password_hash(data['password']).decode('utf-8')

        # Create username from first and last name
        display_name = f"{data['first_name'].capitalize()} {data['last_name'].capitalize()}"
        
        try:
            # Parse dates
            date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
        except ValueError:
            return {'message': "Invalid date format. Use YYYY-MM-DD"}, 400
        
        # Role mapping and determination
        role_mapping = {
            'admin': 'admin',
            'manager': 'manager',
            'hr': 'hr'
        }
        default_role = role_mapping.get(data['position'].lower(), 'employee')
        user_role = data.get('role', default_role)

        try:
            # Create a new employee
            new_employee = Employee(
                first_name=data['first_name'],
                last_name=data['last_name'],
                date_of_birth=date_of_birth,
                phone=data['phone'],
                email=data['email'],
                gender=data['gender'],
                address=data['address'],
                hire_date=hire_date,
                position=data['position'],
                salary=data['salary']
            )
            db.session.add(new_employee)
            db.session.flush()  # Get the employee_id before committing

            # For manager positions, validate department assignment
            if data['position'].lower() == 'manager':
                # Department ID is required for managers
                if not data.get('department_id'):
                    return {'message': "Department ID is required for manager position"}, 400
                
                # Verify department exists
                department = Department.query.filter_by(department_id=data['department_id']).first()
                if not department:
                    return {'message': "Invalid department ID"}, 404
                
                # Check if department already has a manager
                if department.manager:
                    return {'message': "Department already has a manager"}, 400
                
                # Set employee's department
                new_employee.department_id = data['department_id']
                
                # Update department with new manager
                department.manager_id = new_employee.employee_id

            # Create the user account with role
            new_user = User(
                username=display_name,
                email=data['email'],
                password=hashed_password,
                employee_id=new_employee.employee_id,
                role=user_role  # Explicitly set role
            )
            db.session.add(new_user)
            db.session.commit()

            # Generate JWT token with role
            access_token = create_access_token(
                identity=new_user.user_id,
                additional_claims={
                    'username': display_name,
                    'position': data['position'],
                    'role': user_role
                }
            )

            return {
                "message": "User registered successfully",
                "access_token": access_token,
                "username": display_name,
                "position": data['position'],
                "role": user_role
            }, 201

        except Exception as e:
            db.session.rollback()
            return {"message": f"An error occurred while registering: {str(e)}"}, 500

class LoginResource(Resource):
    """
    Login resource for handling user login operations with role support.
    """
    parser = reqparse.RequestParser()
    parser.add_argument('email', type=str, required=True, help='Email address is required to login')
    parser.add_argument('password', type=str, required=True, help='Password is required to login')

    def post(self):
        data = self.parser.parse_args()
        user = User.query.filter_by(email=data['email']).first()
        
        if user is None:
            return {"message": "User not found. Please create an account"}, 404
        
        # Use Bcrypt's check_password_hash instead of comparing directly
        if check_password_hash(user.password, data['password']):
            # Get the employee's position
            employee = Employee.query.filter_by(employee_id=user.employee_id).first()
            
            # Generate JWT token with additional claims including role
            access_token = create_access_token(
                identity=user.user_id,
                additional_claims={
                    'username': user.username,
                    'position': employee.position,
                    'role': user.role  # Include user's role
                }
            )
            return {
                'access_token': access_token,
                'user': {
                    'id': user.user_id,
                    'email': user.email,
                    'position': employee.position,
                    'username': user.username,
                    'role': user.role  # Return role in response
                },
                'message': 'Logged in successfully'
            }, 200
        else:
            return {'message': 'Invalid credentials'}, 401