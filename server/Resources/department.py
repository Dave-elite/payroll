from flask_restful import Resource, reqparse
from models import Employee, Department, User, db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity


class DepartmentResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('department', type=str, required=True, help='Department name required')

    def get(self, id=None):
        if id is None:
            departments = Department.query.all()
            return [department.to_dict() for department in departments], 200
        department = Department.query.filter_by(department_id=id).first()
        if department is None:
            return {'message': 'Department not found'}, 404
        return department.to_dict(), 200