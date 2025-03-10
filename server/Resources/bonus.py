from flask_restful import Resource, reqparse, inputs
from models import Employee, Bonus, db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class BonusResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('bonus_amount', type=float, required=True, help='The bonus amount is required')
    parser.add_argument('employee_name', type=str, required=True, help='Employee name is required')
    parser.add_argument('reason', type=str, required=True, help='The reason for the bonus is required')
    # bonus_date will be auto-set to current date

    @jwt_required()
    def get(self, id=None):
        if id is None:
            bonuses = Bonus.query.all()
            return [
                {
                    **bonus.to_dict(), 
                    'employee_name': f"{bonus.employee.first_name} {bonus.employee.last_name}" 
                    if bonus.employee else None
                } 
                for bonus in bonuses
            ], 200
        
        bonus = Bonus.query.filter_by(bonus_id=id).first()
        if bonus is None:
            return {'message': 'Bonus not found'}, 404
        
        # Include employee details in the response
        bonus_dict = bonus.to_dict()
        if bonus.employee:
            bonus_dict['employee_name'] = f"{bonus.employee.first_name} {bonus.employee.last_name}"
            bonus_dict['employee_email'] = bonus.employee.email
        
        return bonus_dict, 200

    @jwt_required()
    def post(self):
        data = self.parser.parse_args()
        
        try:
            # Validate bonus amount
            if data['bonus_amount'] <= 0:
                return {'message': 'Bonus amount must be greater than zero'}, 400

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
            
            # Create bonus with current date
            bonus = Bonus(
                employee_id=employee.employee_id,  # Assign the employee ID of the found employee
                bonus_amount=data['bonus_amount'],
                bonus_date=datetime.now().date(),  # Automatically set to current date
                reason=data['reason']
            )
            
            db.session.add(bonus)
            db.session.commit()
            
            # Prepare response with employee details
            response = bonus.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            
            return response, 201
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error creating the bonus', 'error': str(e)}, 500

    @jwt_required()
    def put(self, id):
        # For PUT we'll create a different parser that uses employee_id
        put_parser = reqparse.RequestParser()
        put_parser.add_argument('bonus_amount', type=float, required=True, help='The bonus amount is required')
        put_parser.add_argument('employee_id', type=int, required=True, help='Employee ID is required')
        put_parser.add_argument('reason', type=str, required=True, help='The reason for the bonus is required')
        
        data = put_parser.parse_args()
        
        try:
            bonus = Bonus.query.filter_by(bonus_id=id).first()
            if not bonus:
                return {'message': 'Bonus not found'}, 404
            
            # Validate bonus amount
            if data['bonus_amount'] <= 0:
                return {'message': 'Bonus amount must be greater than zero'}, 400
            
            # Verify that the employee exists
            employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
            if not employee:
                return {'message': 'Employee not found'}, 404
            
            # Update all fields
            bonus.employee_id = data['employee_id']
            bonus.bonus_amount = data['bonus_amount']
            bonus.reason = data['reason']
            # Note: We don't update the bonus_date as it should remain when the bonus was originally created
            
            db.session.commit()
            
            # Prepare response with employee details
            response = bonus.to_dict()
            response['employee_name'] = f"{employee.first_name} {employee.last_name}"
            
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the bonus', 'error': str(e)}, 500

    @jwt_required()
    def patch(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('bonus_amount', type=float)
        parser.add_argument('employee_id', type=int)
        parser.add_argument('reason', type=str)
        data = parser.parse_args()
        
        try:
            bonus = Bonus.query.filter_by(bonus_id=id).first()
            if not bonus:
                return {'message': 'Bonus not found'}, 404
            
            # Partial update - only update fields that are provided
            if data['bonus_amount'] is not None:
                if data['bonus_amount'] <= 0:
                    return {'message': 'Bonus amount must be greater than zero'}, 400
                bonus.bonus_amount = data['bonus_amount']
            
            if data['employee_id'] is not None:
                employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
                if not employee:
                    return {'message': 'Employee not found'}, 404
                bonus.employee_id = data['employee_id']
            
            if data['reason'] is not None:
                bonus.reason = data['reason']
            
            db.session.commit()
            
            # Prepare response with employee details
            response = bonus.to_dict()
            if bonus.employee:
                response['employee_name'] = f"{bonus.employee.first_name} {bonus.employee.last_name}"
            
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the bonus', 'error': str(e)}, 500

    @jwt_required()
    def delete(self, id):
        try:
            bonus = Bonus.query.filter_by(bonus_id=id).first()
            if not bonus:
                return {'message': 'Bonus not found'}, 404
            
            db.session.delete(bonus)
            db.session.commit()
            
            return {'message': 'Bonus deleted successfully'}, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error deleting the bonus', 'error': str(e)}, 500