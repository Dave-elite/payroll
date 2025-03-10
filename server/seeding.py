# Import necessary modules
from datetime import datetime, timedelta
import random
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

    departments = [
        {"department_name": "Administration"},
        {"department_name": "Produce"},
        {"department_name": "Bakery"},
        {"department_name": "Pharmacy"},
        {"department_name": "Customer Service"},
        {"department_name": "Electronics"},
        {"department_name": "Marketing"},
        {"department_name": "Beauty"},
        {"department_name": "Beverages"},
    ]
    
    #inserting department objects
    department_objects = []
    try:
        print("Seeding departments...")
        for dept_data in departments:
            # ** is the unpacking operator it allows us to take the keys and values of the dictionary and pass them as individual keyword arguments to a function class constructor
            
            department = Department(**dept_data)
            db.session.add(department)
            department_objects.append(department)

        #flush to get IDs but don't commit yet
        db.session.flush()
        print(f"{len(department_objects)} departments added")
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred seeding departments: {e}")
        exit(1)

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

    # Admin employee creation
    admin = None
    try:
        # Create Admin Employee
        # Unpack dictionary to create Employee instance
        admin = Employee(**employee_admin[0])
        # Assign department_id to the admin employee
        admin.department_id = department_objects[0].department_id
        db.session.add(admin)
        db.session.flush()  # Flush to get employee_id

        # Set Department Manager
        # Make the admin employee the manager of the Administration department
        department_objects[0].manager_id = admin.employee_id

        # Create Admin User Account
        # Create associated user account for authentication
        admin_user = User(
            # Generate username from first and last name
            username=f"{admin.first_name.lower()}.{admin.last_name.lower()}",
            # Use same email as employee record
            email=admin.email,
            # Hash the password with bcrypt
            password=bcrypt.generate_password_hash("Admin@123").decode('utf-8'),
            # Set admin role
            role="admin",
            # Link to employee record
            employee_id=admin.employee_id
        )
        db.session.add(admin_user)
        print("Admin employee and user created successfully!")
    except Exception as e:
        # Rollback all changes if any error occurs
        db.session.rollback()
        print(f"Error occurred creating admin: {e}")
        exit(1)
    
    # Create additional employees
    print("Seeding additional employees...")
    
    # Array to store all employees including admin
    all_employees = [admin]
    
    # Employee data with supermarket-relevant positions
    employee_data = [
        {
            'first_name': 'Sarah',
            'last_name': 'Kimani',
            'date_of_birth': datetime(1992, 5, 15),
            'phone': '+254722123456',
            'email': 'sarah.kimani@example.com',
            'gender': 'Female',
            'address': '456 Market St, Nairobi',
            'hire_date': datetime(2022, 3, 10),
            'position': 'Produce Manager',
            'salary': 42000,
            'department_id': department_objects[1].department_id  # Produce
        },
        {
            'first_name': 'John',
            'last_name': 'Mwangi',
            'date_of_birth': datetime(1988, 8, 22),
            'phone': '+254733987654',
            'email': 'john.mwangi@example.com',
            'gender': 'Male',
            'address': '789 Baker Ave, Mombasa',
            'hire_date': datetime(2021, 11, 5),
            'position': 'Head Baker',
            'salary': 40000,
            'department_id': department_objects[2].department_id  # Bakery
        },
        {
            'first_name': 'Mary',
            'last_name': 'Wanjiku',
            'date_of_birth': datetime(1990, 3, 12),
            'phone': '+254755123789',
            'email': 'mary.wanjiku@example.com',
            'gender': 'Female',
            'address': '101 Health Rd, Nakuru',
            'hire_date': datetime(2022, 1, 15),
            'position': 'Pharmacy Technician',
            'salary': 45000,
            'department_id': department_objects[3].department_id  # Pharmacy
        },
        {
            'first_name': 'Peter',
            'last_name': 'Ochieng',
            'date_of_birth': datetime(1993, 12, 5),
            'phone': '+254799456123',
            'email': 'peter.ochieng@example.com',
            'gender': 'Male',
            'address': '222 Service Lane, Kisumu',
            'hire_date': datetime(2022, 6, 20),
            'position': 'Customer Service Lead',
            'salary': 38000,
            'department_id': department_objects[4].department_id  # Customer Service
        },
        {
            'first_name': 'Grace',
            'last_name': 'Achieng',
            'date_of_birth': datetime(1989, 7, 30),
            'phone': '+254711567890',
            'email': 'grace.achieng@example.com',
            'gender': 'Female',
            'address': '345 Tech Blvd, Eldoret',
            'hire_date': datetime(2021, 5, 12),
            'position': 'Electronics Specialist',
            'salary': 43000,
            'department_id': department_objects[5].department_id  # Electronics
        },
        {
            'first_name': 'James',
            'last_name': 'Otieno',
            'date_of_birth': datetime(1991, 9, 18),
            'phone': '+254744789123',
            'email': 'james.otieno@example.com',
            'gender': 'Male',
            'address': '567 Ad Street, Nairobi',
            'hire_date': datetime(2022, 4, 3),
            'position': 'Marketing Coordinator',
            'salary': 41000,
            'department_id': department_objects[6].department_id  # Marketing
        },
        {
            'first_name': 'Lucy',
            'last_name': 'Njeri',
            'date_of_birth': datetime(1994, 2, 25),
            'phone': '+254766321654',
            'email': 'lucy.njeri@example.com',
            'gender': 'Female',
            'address': '678 Beauty Ave, Mombasa',
            'hire_date': datetime(2023, 1, 10),
            'position': 'Beauty Consultant',
            'salary': 37000,
            'department_id': department_objects[7].department_id  # Beauty
        },
        {
            'first_name': 'Samuel',
            'last_name': 'Kamau',
            'date_of_birth': datetime(1987, 11, 8),
            'phone': '+254788654321',
            'email': 'samuel.kamau@example.com',
            'gender': 'Male',
            'address': '901 Drink St, Nakuru',
            'hire_date': datetime(2022, 2, 15),
            'position': 'Beverage Specialist',
            'salary': 39000,
            'department_id': department_objects[8].department_id  # Beverages
        }
    ]
    
    # Create employees
    try:
        for emp_data in employee_data:
            employee = Employee(**emp_data)
            db.session.add(employee)
            all_employees.append(employee)
        
        # Flush to get employee IDs
        db.session.flush()
        
        # Set department managers
        for i, dept in enumerate(department_objects[1:], 1):
            # Set each department manager to the first employee in that department
            dept.manager_id = all_employees[i].employee_id
            
        print(f"{len(all_employees)-1} additional employees added")
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred creating employees: {e}")
        exit(1)
    
    # Create user accounts for all employees except admin (already created)
    print("Creating user accounts for employees...")
    try:
        for employee in all_employees[1:]:  # Skip admin
            user = User(
                username=f"{employee.first_name.lower()}.{employee.last_name.lower()}",
                email=employee.email,
                password=bcrypt.generate_password_hash("Employee@123").decode('utf-8'),
                role="user",
                employee_id=employee.employee_id
            )
            db.session.add(user)
        print(f"{len(all_employees)-1} user accounts created")
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred creating user accounts: {e}")
        exit(1)
    
    print("Start seeding the attendance...")
    
    # Generate attendance records for the past 30 days
    try:
        current_date = datetime.now().date()
        attendance_count = 0
        
        for day in range(30):
            date = current_date - timedelta(days=day)
            
            # Skip weekends (5=Saturday, 6=Sunday)
            if date.weekday() >= 5:
                continue
                
            for employee in all_employees:
                # Generate random attendance (85% present, 10% late, 5% absent)
                rand_value = random.random()
                
                if rand_value < 0.85:  # Present
                    # Normal working hours (8:00-9:00 AM to 5:00-6:00 PM)
                    clock_in_hour = random.randint(8, 9)
                    clock_in_minute = random.randint(0, 59)
                    clock_in_time = f"{clock_in_hour:02d}:{clock_in_minute:02d}"
                    
                    clock_out_hour = random.randint(17, 18)
                    clock_out_minute = random.randint(0, 59)
                    clock_out_time = f"{clock_out_hour:02d}:{clock_out_minute:02d}"
                    
                    status = "Present"
                    
                    attendance = Attendance(
                        employee_id=employee.employee_id,
                        date=date,
                        clock_in_time=clock_in_time,
                        clock_out_time=clock_out_time,
                        status=status
                    )
                    db.session.add(attendance)
                    attendance_count += 1
                    
                elif rand_value < 0.95:  # Late
                    # Late arrival (9:30-10:30 AM)
                    clock_in_hour = random.randint(9, 10)
                    clock_in_minute = random.randint(30, 59)
                    clock_in_time = f"{clock_in_hour:02d}:{clock_in_minute:02d}"
                    
                    # Normal departure
                    clock_out_hour = random.randint(17, 18)
                    clock_out_minute = random.randint(0, 59)
                    clock_out_time = f"{clock_out_hour:02d}:{clock_out_minute:02d}"
                    
                    attendance = Attendance(
                        employee_id=employee.employee_id,
                        date=date,
                        clock_in_time=clock_in_time,
                        clock_out_time=clock_out_time,
                        status="Late"
                    )
                    db.session.add(attendance)
                    attendance_count += 1
                    
                else:  # Absent - create leave record
                    # Create leave record lasting 1-3 days
                    leave_duration = random.randint(1, 3)
                    leave_type = random.choice(["Sick Leave", "Personal Leave", "Vacation", "Family Emergency"])
                    leave_status = random.choice(["Approved", "Pending"])
                    
                    # Application date is typically a few days before the start date for planned leave
                    # For sick leave or emergencies, it might be the same day
                    application_offset = 0
                    if leave_type in ["Vacation", "Personal Leave"]:
                        application_offset = random.randint(3, 10)  # Applied 3-10 days before
                    
                    application_date = date - timedelta(days=application_offset)
                    
                    # Check if there's already a leave record for this employee within this period
                    existing_leave = False
                    # Skip creating leave if it's within another leave period
                    
                    if not existing_leave:
                        leave = Leave(
                            employee_id=employee.employee_id,
                            leave_type=leave_type,
                            application_date=application_date,
                            start_date=date,
                            end_date=date + timedelta(days=leave_duration-1),
                            status=leave_status
                        )
                        db.session.add(leave)
        
        print(f"{attendance_count} attendance records created")
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred creating attendance records: {e}")
        exit(1)
    
    # Generate payroll records
    print("Seeding payroll records...")
    try:
        payroll_count = 0
        current_date = datetime.now().date()
        
        # Create 3 months of payroll data
        for month in range(3):
            # Calculate pay date (last day of month)
            pay_month = current_date.month - month
            pay_year = current_date.year
            
            if pay_month <= 0:
                pay_month += 12
                pay_year -= 1
                
            # Simplistic approach to find month end
            if pay_month in [1, 3, 5, 7, 8, 10, 12]:
                last_day = 31
            elif pay_month in [4, 6, 9, 11]:
                last_day = 30
            else:  # February, ignoring leap years
                last_day = 28
                
            pay_date = datetime(pay_year, pay_month, last_day)
            
            # Create payroll for each employee
            for employee in all_employees:
                # Monthly base salary (annual / 12)
                base_salary = employee.salary / 12
                
                # Random overtime (0-20 hours)
                overtime_hours = random.uniform(0, 20)
                hourly_rate = (employee.salary / 12) / 160  # Approx. hours per month
                overtime_pay = round(overtime_hours * hourly_rate * 1.5, 2)  # 1.5x regular rate
                
                # Random bonus (20% chance)
                bonus_amount = 0
                if random.random() < 0.2:
                    bonus_amount = round(random.uniform(5000, 15000), 2)
                    
                    # Create bonus record if bonus given
                    bonus_reasons = [
                        "Performance Excellence",
                        "Sales Target Achievement",
                        "Customer Satisfaction Award",
                        "Employee of the Month",
                        "Special Project Completion"
                    ]
                    
                    bonus = Bonus(
                        employee_id=employee.employee_id,
                        bonus_amount=bonus_amount,
                        bonus_date=pay_date,
                        reason=random.choice(bonus_reasons)
                    )
                    db.session.add(bonus)
                
                # Tax calculation (simplified)
                tax_rate = 0.15  # 15% tax rate
                tax_amount = round((base_salary + overtime_pay) * tax_rate, 2)
                
                # Create or update tax record for this year
                if month == 0:  # Only create tax record once per year
                    tax = Tax(
                        employee_id=employee.employee_id,
                        tax_percentage=tax_rate * 100,
                        tax_amount=tax_amount * 12,  # Annual estimated tax
                        year=pay_year
                    )
                    db.session.add(tax)
                
                # Total pay calculation
                total_pay = base_salary + overtime_pay + bonus_amount - tax_amount
                
                # Create payroll record
                payroll = Payroll(
                    employee_id=employee.employee_id,
                    pay_date=pay_date,
                    base_salary=base_salary,
                    overtime=overtime_pay,
                    deductions=tax_amount,
                    bonuses=bonus_amount,
                    total_pay=total_pay
                )
                db.session.add(payroll)
                payroll_count += 1
        
        print(f"{payroll_count} payroll records created")
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred creating payroll records: {e}")
        exit(1)
    
    # Generate leave records (in addition to absence-based ones)
    print("Seeding planned leave records...")
    try:
        leave_count = 0
        current_date = datetime.now().date()
        
        # Create some future planned leaves for employees
        for employee in all_employees:
            # 70% chance employee has planned future leave
            if random.random() < 0.7:
                # Leave starts in the next 1-30 days
                start_offset = random.randint(1, 30)
                leave_start = current_date + timedelta(days=start_offset)
                
                # Leave duration 1-14 days
                leave_duration = random.randint(1, 14)
                leave_end = leave_start + timedelta(days=leave_duration-1)
                
                # Application date is typically 1-14 days before the start date
                application_offset = random.randint(1, 14)
                application_date = leave_start - timedelta(days=application_offset)
                
                # Leave type and status
                leave_type = random.choice(["Vacation", "Personal Leave", "Training Leave", "Medical Leave"])
                
                leave = Leave(
                    employee_id=employee.employee_id,
                    leave_type=leave_type,
                    application_date=application_date,
                    start_date=leave_start,
                    end_date=leave_end,
                    status="Approved" if leave_type == "Vacation" else "Pending"
                )
                db.session.add(leave)
                leave_count += 1
        
        print(f"{leave_count} planned leave records created")
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred creating leave records: {e}")
        exit(1)
    
    # Commit all changes
    try:
        db.session.commit()
        print("All database seed data committed successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred during final commit: {e}")
        exit(1)
    
    print("Database seeding completed successfully!")