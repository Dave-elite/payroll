from flask_restful import Resource, reqparse
class AttendanceResource(Resource):
    """
    Attendance resource for handling employee attendance operations.
    """
    parser = reqparse.RequestParser()
    