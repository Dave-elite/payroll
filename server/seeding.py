# Import necessary modules
from datetime import datetime
from app import app  # Import Flask app instance
from models import db, Employee, Department, Payroll, Attendance, Leave, Tax, Bonus, User  # Import all models
from flask_bcrypt import Bcrypt  # For password hashing

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt()

# Use app context for database operations
with app.app_context():
    print("Start seeding process...")

    # Clear all existing data from tables
    # Delete in specific order to avoid foreign key constraint violations
    try:
        # Delete User records first since they reference Employee
        db.session.query(User).delete()
        # Delete Employee-related records
        db.session.query(Employee).delete()
        # Delete Department records
        db.session.query(Department).delete()
        # Delete all transaction/record tables
        db.session.query(Payroll).delete()
        db.session.query(Attendance).delete()
        db.session.query(Leave).delete()
        db.session.query(Tax).delete()
        db.session.query(Bonus).delete()
        print("Initial data deleted successfully!!!")
    except Exception as e:
        # Rollback transaction if any error occurs
        db.session.rollback()
        print(f"Error occurred deleting the initial data: {e}")

    # Define admin employee data
    print("Seeding the Employee admin...")
    employee_admin = [
        {
            'first_name': 'David',
            'last_name': 'Njenga',
            'date_of_birth': datetime(1990, 1, 1),
            'phone': '+254706199926',
            'email': 'davenjenga098@gmail.com',
            'gender': 'Male',
            'address': '123 Main St, New York, NY',
            'hire_date': datetime(2021, 1, 1),
            'position': 'System Administrator',
            'salary': 50000
        }
    ]

    try:
        # Step 1: Create Administration Department
        # This needs to be created first as Employee needs a department_id
        department = Department(
            department_name="Administration"
        )
        db.session.add(department)
        db.session.flush()  # Flush to get department_id

        # Step 2: Create Admin Employee
        # Unpack dictionary to create Employee instance
        admin = Employee(**employee_admin[0])
        # Assign department_id to the admin employee
        admin.department_id = department.department_id
        db.session.add(admin)
        db.session.flush()  # Flush to get employee_id

        # Step 3: Set Department Manager
        # Make the admin employee the manager of the Administration department
        department.manager_id = admin.employee_id

        # Step 4: Create Admin User Account
        # Create associated user account for authentication
        admin_user = User(
            # Generate username from first and last name
            username=f"{admin.first_name.lower()}.{admin.last_name.lower()}",
            # Use same email as employee record
            email=admin.email,
            # Hash the password with bcrypt
            password_hash=bcrypt.generate_password_hash("Admin@123").decode('utf-8'),
            # Set admin role
            role="admin",
            # Link to employee record
            employee_id=admin.employee_id
        )
        db.session.add(admin_user)
        
        # Commit all changes to database
        db.session.commit()
        print("Admin employee and user created successfully!")

    except Exception as e:
        # Rollback all changes if any error occurs
        db.session.rollback()
        print(f"Error occurred creating admin: {e}")