from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Initialize Flask app and SQLAlchemy
metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(10000), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"), unique=True)

    #Relationships
    #user and the employee will have a one to one relationship the user can be either the staff or the admin of which both of them are employees
    employee = db.relationship('Employee',back_populates = 'user')


class Employee(db.Model, SerializerMixin):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
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

#Relationship
user = db.relationship('User', back_populates='employee')

class Department(db.Model, SerializerMixin):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False)

class Payroll(db.Model, SerializerMixin):
    __tablename__ = 'payroll'

    id = db.Column(db.Integer, primary_key=True)
    pay_date = db.Column(db.Date(), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    overtime_hours = db.Column(db.Integer)
    overtime_pay_per_hour = db.Column(db.Float)
    total_overtime = db.Column(db.Float, default=0.0)
    deductions = db.Column(db.Float, nullable=False, default=0.0)
    bonuses = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float, nullable=False, default=0.0)

class Attendance(db.Model, SerializerMixin):
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.DateTime, nullable=False)
    clock_in_time = db.Column(db.String(100), nullable=False)
    clock_out_time = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)


class Leave(db.Model, SerializerMixin):
    __tablename__ = 'leaves'

    id = db.Column(db.Integer, primary_key=True)
    leave_type = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date(), nullable=False)
    end_date = db.Column(db.Date(), nullable=False)
    approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.String(100))
    approved_date = db.Column(db.Date())

class Tax(db.Model, SerializerMixin):
    __tablename__ = 'taxes'

    id = db.Column(db.Integer, primary_key=True)
    tax_percentage = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)


class Bonus(db.Model, SerializerMixin):
    __tablename__ = 'bonuses'

    id = db.Column(db.Integer, primary_key=True)
    bonus_amount = db.Column(db.Float, nullable=False)
    bonus_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(300), nullable=False)


