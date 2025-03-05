from flask_restful import Resource, reqparse, inputs
from models import Employee, Department, User, db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

class DepartmentResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('department_name', type=str, required=False, help='Department name')
    parser.add_argument('manager_id', type=int, required=False, help='Manager ID for the department')

    @jwt_required()
    def get(self, id=None):
        if id is None:
            departments = Department.query.all()
            return [
                {
                    **department.to_dict(), 
                    'manager_name': f"{department.manager.first_name} {department.manager.last_name}" 
                    if department.manager else None
                } 
                for department in departments
            ], 200
        
        department = Department.query.filter_by(department_id=id).first()
        if department is None:
            return {'message': 'Department not found'}, 404
        
        # Include manager details in the response
        dept_dict = department.to_dict()
        if department.manager:
            dept_dict['manager_name'] = f"{department.manager.first_name} {department.manager.last_name}"
            dept_dict['manager_email'] = department.manager.email
        
        return dept_dict, 200

    @jwt_required()
    def post(self):
        data = self.parser.parse_args()
        
        try:
            # Validate department name
            if not data['department_name']:
                return {'message': 'Department name is required'}, 400

            # Check if department name already exists
            existing_dept = Department.query.filter_by(department_name=data['department_name']).first()
            if existing_dept:
                return {'message': 'Department with this name already exists'}, 400

            # Check if manager_id is provided
            if data['manager_id']:
                # Verify that the manager exists
                manager = Employee.query.filter_by(employee_id=data['manager_id']).first()
                if not manager:
                    return {'message': 'Manager not found'}, 404
                
                # Check if manager is already managing another department
                existing_managed_dept = Department.query.filter_by(manager_id=data['manager_id']).first()
                if existing_managed_dept:
                    return {
                        'message': 'Manager is already assigned to another department', 
                        'existing_department': existing_managed_dept.department_name
                    }, 400
                
                # Create department with manager
                department = Department(
                    department_name=data['department_name'],
                    manager_id=data['manager_id']
                )
            else:
                # Create department without a manager
                department = Department(
                    department_name=data['department_name']
                )
            
            db.session.add(department)
            db.session.commit()
            
            # Prepare response with manager details if exists
            response = department.to_dict()
            if department.manager:
                response['manager_name'] = f"{department.manager.first_name} {department.manager.last_name}"
            
            return response, 201
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error creating the department', 'error': str(e)}, 500

    @jwt_required()
    def put(self, id):
        data = self.parser.parse_args()
        
        try:
            department = Department.query.filter_by(department_id=id).first()
            if not department:
                return {'message': 'Department not found'}, 404
            
            # Validate department name if provided
            if data['department_name']:
                # Check if department name already exists (excluding current department)
                existing_dept = Department.query.filter(
                    Department.department_name == data['department_name'], 
                    Department.department_id != id
                ).first()
                if existing_dept:
                    return {'message': 'Department with this name already exists'}, 400
                
                department.department_name = data['department_name']
            
            # If manager_id is provided, update the manager
            if data['manager_id']:
                manager = Employee.query.filter_by(employee_id=data['manager_id']).first()
                if not manager:
                    return {'message': 'Manager not found'}, 404
                
                # Check if the manager is already managing another department
                existing_managed_dept = Department.query.filter(
                    Department.manager_id == data['manager_id'], 
                    Department.department_id != id
                ).first()
                if existing_managed_dept:
                    return {
                        'message': 'Manager is already assigned to another department', 
                        'existing_department': existing_managed_dept.department_name
                    }, 400
                
                department.manager_id = data['manager_id']
            
            db.session.commit()
            
            # Prepare response with manager details
            response = department.to_dict()
            if department.manager:
                response['manager_name'] = f"{department.manager.first_name} {department.manager.last_name}"
            
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the department', 'error': str(e)}, 500

    @jwt_required()
    def patch(self, id):
        data = self.parser.parse_args()
        
        try:
            department = Department.query.filter_by(department_id=id).first()
            if not department:
                return {'message': 'Department not found'}, 404
            
            # Partial update - only update fields that are provided
            if data['department_name']:
                # Check if department name already exists (excluding current department)
                existing_dept = Department.query.filter(
                    Department.department_name == data['department_name'], 
                    Department.department_id != id
                ).first()
                if existing_dept:
                    return {'message': 'Department with this name already exists'}, 400
                
                department.department_name = data['department_name']
            
            if data['manager_id'] is not None:
                # If manager_id is explicitly set to None, remove the current manager
                if data['manager_id'] is None:
                    department.manager_id = None
                else:
                    # Verify the new manager exists
                    manager = Employee.query.filter_by(employee_id=data['manager_id']).first()
                    if not manager:
                        return {'message': 'Manager not found'}, 404
                    
                    # Check if the manager is already managing another department
                    existing_managed_dept = Department.query.filter(
                        Department.manager_id == data['manager_id'], 
                        Department.department_id != id
                    ).first()
                    if existing_managed_dept:
                        return {
                            'message': 'Manager is already assigned to another department', 
                            'existing_department': existing_managed_dept.department_name
                        }, 400
                    
                    department.manager_id = data['manager_id']
            
            db.session.commit()
            
            # Prepare response with manager details
            response = department.to_dict()
            if department.manager:
                response['manager_name'] = f"{department.manager.first_name} {department.manager.last_name}"
            
            return response, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error updating the department', 'error': str(e)}, 500

    @jwt_required()
    def delete(self, id):
        try:
            department = Department.query.filter_by(department_id=id).first()
            if not department:
                return {'message': 'Department not found'}, 404
            
            # Check if department has any employees
            if department.employees:
                return {'message': 'Cannot delete department with existing employees'}, 400
            
            db.session.delete(department)
            db.session.commit()
            
            return {'message': 'Department deleted successfully'}, 200
        
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error deleting the department', 'error': str(e)}, 500