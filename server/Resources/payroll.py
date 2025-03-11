from flask_restful import Resource, reqparse, inputs
from models import Employee, Payroll,User, db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime

class PayrollResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('employee_name', type=str, required=True, help='Employee name is required')
    parser.add_argument('pay_date', type=str, required=True, help='Pay date is required')
    parser.add_argument('base_salary', type=float, required=True, help='Base salary is required')
    parser.add_argument('overtime', type=float, required=False, default=0.0, help='Overtime pay (defaults to 0.0 if not provided)')
    parser.add_argument('deductions', type=float, required=False, default=0.0, help='Deductions (defaults to 0.0 if not provided)')
    parser.add_argument('bonuses', type=float, required=False, default=0.0, help='Bonuses (defaults to 0.0 if not provided)')

    @jwt_required()
    def get(self, id=None):
        # Get current user's identity and claims
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        # Get the current user
        current_user = User.query.get(current_user_id)
        if not current_user:
            return {'message': 'User not found'}, 404

        # Check if user is admin
        is_admin = current_user.role == 'admin'
        
        # Admin can access all records
        if is_admin:
            # If ID is provided, get specific record
            if id is not None:
                payroll = Payroll.query.filter_by(payroll_id=id).first()
                if payroll is None:
                    return {'message': 'Payroll record not found'}, 404
                
                # Include employee details in the response
                payroll_dict = payroll.to_dict()
                if payroll.employee:
                    payroll_dict['employee_name'] = f"{payroll.employee.first_name} {payroll.employee.last_name}"
                    payroll_dict['employee_email'] = payroll.employee.email
                
                return payroll_dict, 200
            # Otherwise get all records
            else:
                payrolls = Payroll.query.all()
                return [
                    {
                        **payroll.to_dict(), 
                        'employee_name': f"{payroll.employee.first_name} {payroll.employee.last_name}" 
                        if payroll.employee else None
                    } 
                    for payroll in payrolls
                ], 200
        
        # For non-admin users, always return their own payroll records
        # Get the employee record for the logged-in user
        employee = Employee.query.filter_by(employee_id=current_user_id).first()
        if not employee:
            return {'message': 'Employee record not found for authenticated user'}, 404
        
        # If specific ID is requested, verify it belongs to the employee
        if id is not None:
            payroll = Payroll.query.filter_by(payroll_id=id, employee_id=current_user_id).first()
            if not payroll:
                return {'message': 'Payroll record not found or you do not have permission to view it'}, 403
            
            payroll_dict = payroll.to_dict()
            payroll_dict['employee_name'] = f"{employee.first_name} {employee.last_name}"
            payroll_dict['employee_email'] = employee.email
            
            return payroll_dict, 200
        
        # Otherwise return all payroll records for this employee
        payrolls = Payroll.query.filter_by(employee_id=current_user_id).all()
        
        # Format the response
        payroll_list = []
        for payroll in payrolls:
            payroll_dict = payroll.to_dict()
            payroll_dict['employee_name'] = f"{employee.first_name} {employee.last_name}"
            payroll_dict['employee_email'] = employee.email
            payroll_list.append(payroll_dict)
        
        return {
            'employee': {
                'name': f"{employee.first_name} {employee.last_name}",
                'email': employee.email,
                'employee_id': employee.employee_id
            },
            'payroll_records': payroll_list
        }, 200

    @jwt_required()
    def post(self):
        # Get current user's identity and claims
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        # Get the current user
        current_user = User.query.get(current_user_id)
        if not current_user:
            return {'message': 'User not found'}, 404

        # Check if user is admin
        is_admin = current_user.role == 'admin'
        
        if not is_admin:
            return {'message': 'Access denied. Only admins can create payroll records'}, 403
            
        data = self.parser.parse_args()
        
        try:
            # Parse pay date
            try:
                pay_date = datetime.strptime(data['pay_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Pay date must be in format YYYY-MM-DD'}, 400
                
            # Get employee by name (search by first and last name)
            employee_name = data['employee_name']
            names = employee_name.split()
            
            if len(names) < 2:
                return {'message': 'Please provide both first and last name'}, 400
                
            first_name = names[0]
            last_name = ' '.join(names[1:])  # Handle multi-word last names
            
            employee = Employee.query.filter(
                Employee.first_name == first_name, 
                Employee.last_name == last_name
            ).first()
            
            if not employee:
                return {'message': 'Employee not found'}, 404
            
            # Calculate total pay
            base_salary = data['base_salary']
            overtime = data['overtime']
            deductions = data['deductions']
            bonuses = data['bonuses']
            total_pay = base_salary + overtime + bonuses - deductions
            
            # Create payroll record
            payroll = Payroll(
                employee_id=employee.employee_id,
                pay_date=pay_date,
                base_salary=base_salary,
                overtime=overtime,
                deductions=deductions,
                bonuses=bonuses,
                total_pay=total_pay
            )
            
            db.session.add(payroll)
            db.session.commit()
            
            # Prepare response with employee details
            response = payroll.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            response['message'] = 'Payroll record added successfully'
            
            return response, 201
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error creating the payroll record', 'error': str(e)}, 500

    @jwt_required()
    def put(self, id):
        # Get current user's identity and claims
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        # Get the current user
        current_user = User.query.get(current_user_id)
        if not current_user:
            return {'message': 'User not found'}, 404

        # Check if user is admin
        is_admin = current_user.role == 'admin'
        
        if not is_admin:
            return {'message': 'Access denied. Only admins can create payroll records'}, 403
        # For PUT we'll create a different parser that uses employee_id
        put_parser = reqparse.RequestParser()
        put_parser.add_argument('employee_id', type=int, required=True, help='Employee ID is required')
        put_parser.add_argument('pay_date', type=str, required=True, help='Pay date is required')
        put_parser.add_argument('base_salary', type=float, required=True, help='Base salary is required')
        put_parser.add_argument('overtime', type=float, required=True, help='Overtime pay is required')
        put_parser.add_argument('deductions', type=float, required=True, help='Deductions are required')
        put_parser.add_argument('bonuses', type=float, required=True, help='Bonuses are required')
        
        data = put_parser.parse_args()
        
        try:
            payroll = Payroll.query.filter_by(payroll_id=id).first()
            if not payroll:
                return {'message': 'Payroll record not found'}, 404

            # Parse pay date
            try:
                pay_date = datetime.strptime(data['pay_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Pay date must be in format YYYY-MM-DD'}, 400
            
            # Verify that the employee exists
            employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
            if not employee:
                return {'message': 'Employee not found'}, 404
            
            # Calculate total pay
            base_salary = data['base_salary']
            overtime = data['overtime']
            deductions = data['deductions']
            bonuses = data['bonuses']
            total_pay = base_salary + overtime + bonuses - deductions
            
            # Update fields
            payroll.employee_id = data['employee_id']
            payroll.pay_date = pay_date
            payroll.base_salary = base_salary
            payroll.overtime = overtime
            payroll.deductions = deductions
            payroll.bonuses = bonuses
            payroll.total_pay = total_pay
            
            db.session.commit()
            
            # Prepare response with employee details
            response = payroll.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            response['message'] = 'Payroll record updated successfully'
            
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the payroll record', 'error': str(e)}, 500

    @jwt_required()
    def patch(self, id):
        # Get current user's identity and claims
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        # Get the current user
        current_user = User.query.get(current_user_id)
        if not current_user:
            return {'message': 'User not found'}, 404

        # Check if user is admin
        is_admin = current_user.role == 'admin'
        
        if not is_admin:
            return {'message': 'Access denied. Only admins can create payroll records'}, 403
        parser = reqparse.RequestParser()
        parser.add_argument('employee_id', type=int)
        parser.add_argument('pay_date', type=str)
        parser.add_argument('base_salary', type=float)
        parser.add_argument('overtime', type=float)
        parser.add_argument('deductions', type=float)
        parser.add_argument('bonuses', type=float)
        
        data = parser.parse_args()
        
        try:
            payroll = Payroll.query.filter_by(payroll_id=id).first()
            if not payroll:
                return {'message': 'Payroll record not found'}, 404
            
            # Track if we need to recalculate total_pay
            recalculate = False
            
            # Partial update - only update fields that are provided
            if data['employee_id'] is not None:
                employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
                if not employee:
                    return {'message': 'Employee not found'}, 404
                payroll.employee_id = data['employee_id']
            
            # Update pay date if provided
            if data['pay_date'] is not None:
                try:
                    payroll.pay_date = datetime.strptime(data['pay_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'Pay date must be in format YYYY-MM-DD'}, 400
                    
            # Update pay components if provided
            if data['base_salary'] is not None:
                payroll.base_salary = data['base_salary']
                recalculate = True
                
            if data['overtime'] is not None:
                payroll.overtime = data['overtime']
                recalculate = True
                
            if data['deductions'] is not None:
                payroll.deductions = data['deductions']
                recalculate = True
                
            if data['bonuses'] is not None:
                payroll.bonuses = data['bonuses']
                recalculate = True
            
            # Recalculate total_pay if any pay component was updated
            if recalculate:
                payroll.total_pay = payroll.base_salary + payroll.overtime + payroll.bonuses - payroll.deductions
            
            db.session.commit()
            
            # Prepare response with employee details
            response = payroll.to_dict()
            if payroll.employee:
                response['employee_name'] = f"{payroll.employee.first_name} {payroll.employee.last_name}"
            response['message'] = 'Payroll record updated successfully'
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the payroll record', 'error': str(e)}, 500

    @jwt_required()
    def delete(self, id):
        # Get current user's identity and claims
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        # Get the current user
        current_user = User.query.get(current_user_id)
        if not current_user:
            return {'message': 'User not found'}, 404

        # Check if user is admin
        is_admin = current_user.role == 'admin'
        
        if not is_admin:
            return {'message': 'Access denied. Only admins can create payroll records'}, 403
        try:
            payroll = Payroll.query.filter_by(payroll_id=id).first()
            if not payroll:
                return {'message': 'Payroll record not found'}, 404
            
            db.session.delete(payroll)
            db.session.commit()
            
            return {'message': 'Payroll record deleted successfully'}, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error deleting the payroll record', 'error': str(e)}, 500