from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Initialize Flask app and SQLAlchemy
metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

class Employee(db.Model):
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

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False)

class Payroll(db.Model):
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

class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.DateTime, nullable=False)
    clock_in_time = db.Column(db.String(100), nullable=False)
    clock_out_time = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)


class Leave(db.Model):
    __tablename__ = 'leaves'

    id = db.Column(db.Integer, primary_key=True)
    leave_type = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date(), nullable=False)
    end_date = db.Column(db.Date(), nullable=False)
    approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.String(100))
    approved_date = db.Column(db.Date())

class Tax(db.Model):
    __tablename__ = 'taxes'

    id = db.Column(db.Integer, primary_key=True)
    tax_percentage = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)


class Bonus(db.Model):
    __tablename__ = 'bonuses'

    id = db.Column(db.Integer, primary_key=True)
    bonus_amount = db.Column(db.Float, nullable=False)
    bonus_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(300), nullable=False)


