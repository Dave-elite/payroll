from flask_restful import Resource, reqparse, inputs
from models import Employee, Leave, db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class LeaveResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('employee_name', type=str, required=True, help='Employee name is required')
    parser.add_argument('leave_type', type=str, required=True, help='Leave type is required')
    parser.add_argument('start_date', type=str, required=True, help='Start date is required')
    parser.add_argument('end_date', type=str, required=True, help='End date is required')
    parser.add_argument('status', type=str, required=False, default='Pending', 
                        help='Status (defaults to Pending if not provided)')

    @jwt_required()
    def get(self, id=None):
        if id is None:
            leaves = Leave.query.all()
            return [
                {
                    **leave.to_dict(), 
                    'employee_name': f"{leave.employee.first_name} {leave.employee.last_name}" 
                    if leave.employee else None
                } 
                for leave in leaves
            ], 200
        
        leave = Leave.query.filter_by(leave_id=id).first()
        if leave is None:
            return {'message': 'Leave request not found'}, 404
        
        # Include employee details in the response
        leave_dict = leave.to_dict()
        if leave.employee:
            leave_dict['employee_name'] = f"{leave.employee.first_name} {leave.employee.last_name}"
            leave_dict['employee_email'] = leave.employee.email
        
        return leave_dict, 200

    @jwt_required()
    def post(self):
        data = self.parser.parse_args()
        
        try:
            # Parse dates
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Dates must be in format YYYY-MM-DD'}, 400
                
            # Validate date range
            if end_date < start_date:
                return {'message': 'End date cannot be before start date'}, 400

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
            
            # Create leave request with current date as application date
            leave = Leave(
                employee_id=employee.employee_id,
                leave_type=data['leave_type'],
                application_date=datetime.now().date(),  # Automatically set to current date
                start_date=start_date,
                end_date=end_date,
                status=data['status']
            )
            
            db.session.add(leave)
            db.session.commit()
            
            # Prepare response with employee details
            response = leave.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            
            return response, 201
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error creating the leave request', 'error': str(e)}, 500

    @jwt_required()
    def put(self, id):
        # For PUT we'll create a different parser that uses employee_id
        put_parser = reqparse.RequestParser()
        put_parser.add_argument('employee_id', type=int, required=True, help='Employee ID is required')
        put_parser.add_argument('leave_type', type=str, required=True, help='Leave type is required')
        put_parser.add_argument('start_date', type=str, required=True, help='Start date is required')
        put_parser.add_argument('end_date', type=str, required=True, help='End date is required')
        put_parser.add_argument('status', type=str, required=True, help='Status is required')
        
        data = put_parser.parse_args()
        
        try:
            leave = Leave.query.filter_by(leave_id=id).first()
            if not leave:
                return {'message': 'Leave request not found'}, 404

            # Parse dates
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Dates must be in format YYYY-MM-DD'}, 400
                
            # Validate date range
            if end_date < start_date:
                return {'message': 'End date cannot be before start date'}, 400
            
            # Verify that the employee exists
            employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
            if not employee:
                return {'message': 'Employee not found'}, 404
            
            # Update fields
            leave.employee_id = data['employee_id']
            leave.leave_type = data['leave_type']
            leave.start_date = start_date
            leave.end_date = end_date
            leave.status = data['status']
            # Note: We don't update the application_date as it should remain when the leave was originally requested
            
            db.session.commit()
            
            # Prepare response with employee details
            response = leave.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the leave request', 'error': str(e)}, 500

    @jwt_required()
    def patch(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('employee_id', type=int)
        parser.add_argument('leave_type', type=str)
        parser.add_argument('start_date', type=str)
        parser.add_argument('end_date', type=str)
        parser.add_argument('status', type=str)
        
        data = parser.parse_args()
        
        try:
            leave = Leave.query.filter_by(leave_id=id).first()
            if not leave:
                return {'message': 'Leave request not found'}, 404
            
            # Partial update - only update fields that are provided
            if data['employee_id'] is not None:
                employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
                if not employee:
                    return {'message': 'Employee not found'}, 404
                leave.employee_id = data['employee_id']
            
            if data['leave_type'] is not None:
                leave.leave_type = data['leave_type']
            
            # Update dates if provided
            if data['start_date'] is not None:
                try:
                    leave.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'Start date must be in format YYYY-MM-DD'}, 400
                    
            if data['end_date'] is not None:
                try:
                    leave.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'End date must be in format YYYY-MM-DD'}, 400
            
            # Validate date range after updates
            if leave.end_date < leave.start_date:
                return {'message': 'End date cannot be before start date'}, 400
            
            if data['status'] is not None:
                leave.status = data['status']
            
            db.session.commit()
            
            # Prepare response with employee details
            response = leave.to_dict()
            if leave.employee:
                response['employee_name'] = f"{leave.employee.first_name} {leave.employee.last_name}"
            
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the leave request', 'error': str(e)}, 500

    @jwt_required()
    def delete(self, id):
        try:
            leave = Leave.query.filter_by(leave_id=id).first()
            if not leave:
                return {'message': 'Leave request not found'}, 404
            
            db.session.delete(leave)
            db.session.commit()
            
            return {'message': 'Leave request deleted successfully'}, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error deleting the leave request', 'error': str(e)}, 500