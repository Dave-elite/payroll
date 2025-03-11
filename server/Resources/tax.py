from flask_restful import Resource, reqparse, inputs
from models import Employee, Tax, User, db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class TaxResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('employee_name', type=str, required=True, help='Employee name is required')
    parser.add_argument('tax_percentage', type=float, required=True, help='Tax percentage is required')
    parser.add_argument('tax_amount', type=float, required=True, help='Tax amount is required')
    parser.add_argument('year', type=int, required=True, help='Tax year is required')

    @jwt_required()
    def get(self, id=None):
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return {'message': 'User not found'}, 404
        
        # Check if current user is admin
        is_admin = current_user.role == 'admin'
        
        # For admin users - return all records or specific record by ID
        if is_admin:
            if id is None:
                tax_records = Tax.query.all()
                return {
                    'message': 'Successfully retrieved all tax records',
                    'data': [
                        {
                            **tax.to_dict(), 
                            'employee_name': f"{tax.employee.first_name} {tax.employee.last_name}" 
                            if tax.employee else None
                        } 
                        for tax in tax_records
                    ]
                }, 200
            
            tax_record = Tax.query.filter_by(tax_id=id).first()
            if tax_record is None:
                return {'message': 'Tax record not found'}, 404
            
            # Include employee details in the response
            tax_dict = tax_record.to_dict()
            if tax_record.employee:
                tax_dict['employee_name'] = f"{tax_record.employee.first_name} {tax_record.employee.last_name}"
                tax_dict['employee_email'] = tax_record.employee.email
            
            return {
                'message': f'Successfully retrieved tax record with ID {id}',
                'data': tax_dict
            }, 200
        
        # For non-admin users - return only their records
        else:
            # Get the employee record for the current user
            employee = Employee.query.filter_by(user_id=current_user_id).first()
            
            if not employee:
                return {'message': 'Employee record not found for current user'}, 404
            
            if id is None:
                # Return all tax records for this employee
                tax_records = Tax.query.filter_by(employee_id=employee.employee_id).all()
                return {
                    'message': 'Successfully retrieved your tax records',
                    'data': [tax.to_dict() for tax in tax_records]
                }, 200
            
            # Return specific tax record for this employee
            tax_record = Tax.query.filter_by(tax_id=id, employee_id=employee.employee_id).first()
            
            if tax_record is None:
                return {'message': 'Tax record not found or you do not have permission to view it'}, 404
            
            return {
                'message': f'Successfully retrieved tax record with ID {id}',
                'data': tax_record.to_dict()
            }, 200

    @jwt_required()
    def post(self):
        # Only admin can create tax records
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return {'message': 'User not found'}, 404
        
        if current_user.role != 'admin':
            return {'message': 'Permission denied. Only admin users can create tax records'}, 403
        
        data = self.parser.parse_args()
        
        try:
            # Validate year
            current_year = datetime.now().year
            if data['year'] < 2000 or data['year'] > current_year + 1:
                return {'message': f'Year must be between 2000 and {current_year + 1}'}, 400
                
            # Validate tax percentage
            if data['tax_percentage'] < 0 or data['tax_percentage'] > 100:
                return {'message': 'Tax percentage must be between 0 and 100'}, 400
                
            # Validate tax amount
            if data['tax_amount'] < 0:
                return {'message': 'Tax amount cannot be negative'}, 400

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
            
            # Check if a tax record already exists for this employee and year
            existing_record = Tax.query.filter_by(
                employee_id=employee.employee_id,
                year=data['year']
            ).first()
            
            if existing_record:
                return {'message': f'Tax record already exists for {employee_name} for year {data["year"]}'}, 409
            
            # Create new tax record
            tax_record = Tax(
                employee_id=employee.employee_id,
                tax_percentage=data['tax_percentage'],
                tax_amount=data['tax_amount'],
                year=data['year']
            )
            
            db.session.add(tax_record)
            db.session.commit()
            
            # Prepare response with employee details
            response = tax_record.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            
            return {
                'message': f'Tax record successfully created for {employee_name} for year {data["year"]}',
                'data': response
            }, 201
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error creating the tax record', 'error': str(e)}, 500

    @jwt_required()
    def put(self, id):
        # Only admin can update tax records
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return {'message': 'User not found'}, 404
        
        if current_user.role != 'admin':
            return {'message': 'Permission denied. Only admin users can update tax records'}, 403
        
        # For PUT we'll create a different parser that uses employee_id
        put_parser = reqparse.RequestParser()
        put_parser.add_argument('employee_id', type=int, required=True, help='Employee ID is required')
        put_parser.add_argument('tax_percentage', type=float, required=True, help='Tax percentage is required')
        put_parser.add_argument('tax_amount', type=float, required=True, help='Tax amount is required')
        put_parser.add_argument('year', type=int, required=True, help='Tax year is required')
        
        data = put_parser.parse_args()
        
        try:
            tax_record = Tax.query.filter_by(tax_id=id).first()
            if not tax_record:
                return {'message': 'Tax record not found'}, 404

            # Validate year
            current_year = datetime.now().year
            if data['year'] < 2000 or data['year'] > current_year + 1:
                return {'message': f'Year must be between 2000 and {current_year + 1}'}, 400
                
            # Validate tax percentage
            if data['tax_percentage'] < 0 or data['tax_percentage'] > 100:
                return {'message': 'Tax percentage must be between 0 and 100'}, 400
                
            # Validate tax amount
            if data['tax_amount'] < 0:
                return {'message': 'Tax amount cannot be negative'}, 400
            
            # Verify that the employee exists
            employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
            if not employee:
                return {'message': 'Employee not found'}, 404
            
            # Check if updating to a different year would create a duplicate
            if tax_record.employee_id == data['employee_id'] and tax_record.year != data['year']:
                existing_record = Tax.query.filter_by(
                    employee_id=data['employee_id'],
                    year=data['year']
                ).first()
                
                if existing_record and existing_record.tax_id != tax_record.tax_id:
                    return {'message': f'Tax record already exists for this employee for year {data["year"]}'}, 409
            
            # Update fields
            tax_record.employee_id = data['employee_id']
            tax_record.tax_percentage = data['tax_percentage']
            tax_record.tax_amount = data['tax_amount']
            tax_record.year = data['year']
            
            db.session.commit()
            
            # Prepare response with employee details
            response = tax_record.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            
            return {
                'message': f'Tax record with ID {id} successfully updated',
                'data': response
            }, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the tax record', 'error': str(e)}, 500

    @jwt_required()
    def patch(self, id):
        # Only admin can partially update tax records
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return {'message': 'User not found'}, 404
        
        if current_user.role != 'admin':
            return {'message': 'Permission denied. Only admin users can update tax records'}, 403
        
        parser = reqparse.RequestParser()
        parser.add_argument('employee_id', type=int)
        parser.add_argument('tax_percentage', type=float)
        parser.add_argument('tax_amount', type=float)
        parser.add_argument('year', type=int)
        
        data = parser.parse_args()
        
        try:
            tax_record = Tax.query.filter_by(tax_id=id).first()
            if not tax_record:
                return {'message': 'Tax record not found'}, 404
            
            # Track what fields were updated for the success message
            updated_fields = []
            
            # Partial update - only update fields that are provided
            if data['employee_id'] is not None:
                employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
                if not employee:
                    return {'message': 'Employee not found'}, 404
                tax_record.employee_id = data['employee_id']
                updated_fields.append('employee')
            
            # Validate and update tax percentage if provided
            if data['tax_percentage'] is not None:
                if data['tax_percentage'] < 0 or data['tax_percentage'] > 100:
                    return {'message': 'Tax percentage must be between 0 and 100'}, 400
                tax_record.tax_percentage = data['tax_percentage']
                updated_fields.append('tax percentage')
            
            # Validate and update tax amount if provided
            if data['tax_amount'] is not None:
                if data['tax_amount'] < 0:
                    return {'message': 'Tax amount cannot be negative'}, 400
                tax_record.tax_amount = data['tax_amount']
                updated_fields.append('tax amount')
            
            # Validate and update year if provided
            if data['year'] is not None:
                current_year = datetime.now().year
                if data['year'] < 2000 or data['year'] > current_year + 1:
                    return {'message': f'Year must be between 2000 and {current_year + 1}'}, 400
                
                # Check if changing year would create a duplicate
                if tax_record.year != data['year']:
                    existing_record = Tax.query.filter_by(
                        employee_id=tax_record.employee_id,
                        year=data['year']
                    ).first()
                    
                    if existing_record and existing_record.tax_id != tax_record.tax_id:
                        return {'message': f'Tax record already exists for this employee for year {data["year"]}'}, 409
                
                tax_record.year = data['year']
                updated_fields.append('year')
            
            # If no fields were provided to update
            if not updated_fields:
                return {'message': 'No fields provided for update'}, 400
            
            db.session.commit()
            
            # Prepare response with employee details
            response = tax_record.to_dict()
            if tax_record.employee:
                response['employee_name'] = f"{tax_record.employee.first_name} {tax_record.employee.last_name}"
            
            # Create success message based on what was updated
            fields_str = ', '.join(updated_fields)
            
            return {
                'message': f'Tax record with ID {id} successfully updated ({fields_str})',
                'data': response
            }, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the tax record', 'error': str(e)}, 500

    @jwt_required()
    def delete(self, id):
        # Only admin can delete tax records
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return {'message': 'User not found'}, 404
        
        if current_user.role != 'admin':
            return {'message': 'Permission denied. Only admin users can delete tax records'}, 403
        
        try:
            tax_record = Tax.query.filter_by(tax_id=id).first()
            if not tax_record:
                return {'message': 'Tax record not found'}, 404
            
            # Get employee details for the success message
            employee = tax_record.employee
            employee_name = f"{employee.first_name} {employee.last_name}" if employee else "Unknown employee"
            tax_year = tax_record.year
            
            db.session.delete(tax_record)
            db.session.commit()
            
            return {
                'message': f'Tax record with ID {id} for {employee_name} (year {tax_year}) deleted successfully'
            }, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error deleting the tax record', 'error': str(e)}, 500