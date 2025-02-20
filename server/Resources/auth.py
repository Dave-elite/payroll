from flask_restful import Resource, reqparse
from flask import request
from models import db, User, Employee, Department
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import generate_password_hash, check_password_hash
import re
from datetime import datetime

class UserResource(Resource):
    """
    User resource for handling user related operations.
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
    parser.add_argument('role', type=str, required=True, help='Role is required')

    def post(self):
        data = self.parser.parse_args()

        #validate the email format 
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, data['email']):
            return {"message": "Invalid email address"}, 400
        #validate phone number and email address uniqueness
        if User.query.filter_by(phone=data['phone']).first():
            return {"message": "Phone number already exists"}, 422
        if User.query.filter_by(email=data['email']).first():
            return {"message": "Email address already exists"}, 422
        #validating password matching
        if data['password'] != data['confirm_password']:
            return {'message': "password does not match "}, 422
        
        hashed_password = generate_password_hash(data['password']).decode('utf-8')

        #creating a username from the first and last_name from the db
        display_name = f"{data['first_name'].capitalize()} {data["last_name"].capitalize()}"
        username = f"{data['first_name'].lower()}.{data['last_name'].lower()}"

        try:
            #datetime.strptime is used parse a string inot datetime given a specific format
            date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()

        except ValueError:
            return {'message': "Invalid date format. Use YYYY-MM-DD"}, 400
        
        #Create a new employee
        new_employee = Employee(
            first_name = data['first_name'],
            last_name = data['last_name'],
            date_of_birth=date_of_birth,
            phone=data['phone'],
            email = data['email'],
            gender = data['gender'],
            address = data['address'],
            hire_date = hire_date,
            position=data['postion'],
            salary = data['salary'] ,
            bonus = data['bonus']           
        )
        db.session.add(new_employee)
        db.session.commit()
    
