from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from datetime import datetime
import re
import uuid

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

class User(db.Model, SerializerMixin):
    """
    User model for system authentication and authorization.
    One-to-One relationship with Employee - each user must be an employee.
    """
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(10000), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='employee')  # Added default role
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"), unique=True)
    
    # One-to-One relationship with Employee
    employee = db.relationship('Employee', back_populates='user', uselist=False)
    
    # Prevents recursive serialization
    serialize_rules = ('-employee',)
    
    @validates('email')
    def validate_email(self, key, value):
        pattern = r'^[a-z,A-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValueError(f"{value} is not a valid email address")
        return value

    def assign_role(self):
        """
        Automatically assign role based on employee position
        """
        if self.employee:
            position_to_role = {
                'manager': 'manager',
                'hr': 'hr',
                'admin': 'admin'
            }
            self.role = position_to_role.get(self.employee.position.lower(), 'employee')

class Employee(db.Model, SerializerMixin):
    """
    Employee model representing staff members.
    Central model with multiple relationships:
    - One-to-One with User
    - Many-to-One with Department
    - Self-referential Many-to-One for supervisor relationship
    - One-to-Many with Payroll, Attendance, Leave, Tax, and Bonus
    """
    __tablename__ = 'employees'
    
    employee_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(55), nullable=False)
    last_name = db.Column(db.String(55), nullable=False)
    date_of_birth = db.Column(db.Date(), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    gender = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    hire_date = db.Column(db.Date(), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    salary = db.Column(db.Float(), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'))

    # Relationships
    user = db.relationship('User', back_populates='employee')
    department = db.relationship('Department', foreign_keys=[department_id], back_populates='employees')
    supervisor = db.relationship('Employee', remote_side=[employee_id], backref='subordinates')
    managed_department = db.relationship('Department', back_populates='manager', foreign_keys='Department.manager_id')
    payrolls = db.relationship('Payroll', back_populates='employee', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', back_populates='employee', cascade='all, delete-orphan')
    leaves = db.relationship('Leave', back_populates='employee', cascade='all, delete-orphan')
    tax_records = db.relationship('Tax', back_populates='employee', cascade='all, delete-orphan')
    bonuses = db.relationship('Bonus', back_populates='employee', cascade='all, delete-orphan')

    # Serialize rules to prevent circular references
    serialize_rules = ('-user', '-department', '-supervisor', '-subordinates', 
                      '-payrolls', '-attendances', '-leaves', '-tax_records', 
                      '-bonuses', '-managed_department')

    @validates('email', 'phone')
    def validate_fields(self, key, value):
        if key == 'email':
            pattern = r'^[a-z,A-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, value):
                raise ValueError(f"{value} is not a valid email address")
        elif key == 'phone':
            pattern = r'^\+?\d{7,12}$'
            if not re.match(pattern, value):
                raise ValueError(f"{value} is not a valid phone number")
        return value

class Department(db.Model, SerializerMixin):
    """
    Department model representing company divisions.
    Has relationships with Employee model:
    - One-to-Many with employees
    - One-to-One with manager (who is an Employee)
    """
    __tablename__ = 'departments'
    
    department_id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(255), nullable=False, unique=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'))
    
    # Relationships
    employees = db.relationship('Employee', back_populates='department', 
                              foreign_keys='Employee.department_id')
    manager = db.relationship('Employee', back_populates='managed_department',
                            foreign_keys=[manager_id])
    
    # Serialize rules
    serialize_rules = ('-employees', '-manager')

class Payroll(db.Model, SerializerMixin):
    """
    Payroll model for tracking employee compensation.
    Many-to-One relationship with Employee.
    """
    __tablename__ = 'payroll'
    
    payroll_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'), nullable=False)
    pay_date = db.Column(db.Date(), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    overtime = db.Column(db.Float, default=0.0)
    deductions = db.Column(db.Float, nullable=False, default=0.0)
    bonuses = db.Column(db.Float, default=0.0)
    total_pay = db.Column(db.Float, nullable=False)
    
    # Relationship with Employee
    employee = db.relationship('Employee', back_populates='payrolls')
    
    # Serialize rules
    serialize_rules = ('-employee',)

class Attendance(db.Model, SerializerMixin):
    """
    Attendance model for tracking employee attendance.
    Many-to-One relationship with Employee.
    """
    __tablename__ = 'attendance'
    
    attendance_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    clock_in_time = db.Column(db.String(100), nullable=False)
    clock_out_time = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(100), nullable=False)
    
    # Relationship with Employee
    employee = db.relationship('Employee', back_populates='attendances')
    
    # Serialize rules
    serialize_rules = ('-employee',)

class Leave(db.Model, SerializerMixin):
    """
    Leave model for managing employee time off.
    Many-to-One relationship with Employee.
    """
    __tablename__ = 'leave'
    
    leave_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'), nullable=False)
    leave_type = db.Column(db.String(100), nullable=False)
    application_date = db.Column(db.Date(), nullable=False)
    start_date = db.Column(db.Date(), nullable=False)
    end_date = db.Column(db.Date(), nullable=False)
    status = db.Column(db.String(100), nullable=False, default='Pending')
    
    # Relationship with Employee
    employee = db.relationship('Employee', back_populates='leaves')
    
    # Serialize rules
    serialize_rules = ('-employee',)

class Tax(db.Model, SerializerMixin):
    """
    Tax model for managing employee tax records.
    Many-to-One relationship with Employee.
    """
    __tablename__ = 'tax'
    
    tax_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'), nullable=False)
    tax_percentage = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    # Relationship with Employee
    employee = db.relationship('Employee', back_populates='tax_records')
    
    # Serialize rules
    serialize_rules = ('-employee',)

class Bonus(db.Model, SerializerMixin):
    """
    Bonus model for tracking employee bonuses.
    Many-to-One relationship with Employee.
    """
    __tablename__ = 'bonus'
    
    bonus_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'), nullable=False)
    bonus_amount = db.Column(db.Float, nullable=False)
    bonus_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(300), nullable=False)
    
    # Relationship with Employee
    employee = db.relationship('Employee', back_populates='bonuses')
    
    # Serialize rules
    serialize_rules = ('-employee',)



class TokenBlacklist(db.Model, SerializerMixin):
    """
    Token blacklist model for managing JWT tokens.
    This model stores tokens that are no longer valid.
    """
    __tablename__ = 'token_blacklist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(36), unique=True, nullable=True)  # Make it nullable initially
    token = db.Column(db.String(500), unique=True, nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Serialize rules
    serialize_rules = ('-revoked_at',)

    def __init__(self, *args, **kwargs):
        # If jti is not provided, generate a unique one
        if 'jti' not in kwargs:
            kwargs['jti'] = str(uuid.uuid4())
        super().__init__(*args, **kwargs)