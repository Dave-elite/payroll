from models import db, Attendance, Employee
from flask_restful import Resource, reqparse
from flask import request
class AttendanceResource(Resource):
    """
    Attendance resource for handling employee attendance operations.
    """
    parser = reqparse.RequestParser()
    parser.add_argument('clock_in_time', type=str, required=True, help='Clock-in time is required')
    parser.add_argument('clock_out_time', type=str, required=True, help='Clock-out time is required')
    parser.add_argument('status', type=str, required=False)

    def get(self, id=None):
        employee_id = Employee.employee_id
        if id is None:
            #fetch all the data for the attendeance record
            attendances = Attendance.query.all()
            return [attendance.to_dict() for attendance in attendances]
        
        #if the attendance id id provided fetch the attendance with the given employee_id
        attendance = Attendance.query.filter_by(employee_id=id).first()
        if attendance:
            return attendance.to_dict(), 200
        return {'message': 'Attendance record not found'}, 404
    