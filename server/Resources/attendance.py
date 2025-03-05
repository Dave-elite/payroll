from models import db, Attendance, Employee
from flask_restful import Resource, reqparse
from flask import request, jsonify
from datetime import date, datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity

class AttendanceResource(Resource):
    """
    Attendance resource for handling employee attendance operations.
    Provides methods for clock-in, clock-out, and retrieving attendance records.
    """
    
    @jwt_required()
    def get(self, id=None):
        """
        Retrieve attendance records.
        If no ID is provided, returns all records.
        If an ID is provided, returns records for that specific employee.
        """
        current_user_id = get_jwt_identity()
        
        if id is None:
            # Fetch all attendance records (might want to restrict this to admin only)
            attendances = Attendance.query.all()
            return [attendance.to_dict() for attendance in attendances], 200
        
        # Fetch attendance records for a specific employee
        attendances = Attendance.query.filter_by(employee_id=id).all()
        if attendances:
            return [attendance.to_dict() for attendance in attendances], 200
        
        return {'message': 'No attendance records found'}, 404

    @jwt_required()
    def post(self):
        """
        Handle clock-in and clock-out operations.
        Automatically determines whether it's a clock-in or clock-out based on existing records.
        """
        current_user_id = get_jwt_identity()
        
        try:
            # Check if there's an existing attendance record for today
            today = date.today()
            existing_attendance = Attendance.query.filter_by(
                employee_id=current_user_id, 
                date=today
            ).first()
            
            # Current time for clock-in/out
            current_time = datetime.now().strftime('%H:%M:%S')
            
            if not existing_attendance:
                # Clock-in operation
                new_attendance = Attendance(
                    employee_id=current_user_id,
                    date=today,
                    clock_in_time=current_time,
                    clock_out_time=None,  # Use None instead of empty string
                    status='Present'
                )
                db.session.add(new_attendance)
                db.session.commit()
                return {
                    'message': 'Clocked in successfully', 
                    'attendance': new_attendance.to_dict()
                }, 201
            
            elif existing_attendance.clock_out_time is None:
                # Clock-out operation
                # Calculate total work hours
                clock_in_time = datetime.strptime(existing_attendance.clock_in_time, '%H:%M:%S')
                clock_out_time = datetime.now()
                
                # Calculate work duration
                work_duration = clock_out_time - datetime.combine(today, clock_in_time.time())
                
                # Update attendance record
                existing_attendance.clock_out_time = current_time
                existing_attendance.status = 'Completed'
                
                # Optional: You might want to add work hours to the model
                # This would require adding a new column to the Attendance model
                # existing_attendance.work_hours = work_duration.total_seconds() / 3600  # Convert to hours
                
                db.session.commit()
                return {
                    'message': 'Clocked out successfully', 
                    'attendance': existing_attendance.to_dict(),
                    'work_duration': str(work_duration)  # Return work duration to frontend
                }, 200
            
            else:
                # Already clocked out for the day
                return {
                    'message': 'You have already clocked in and out for today'
                }, 400
        
        except Exception as e:
            db.session.rollback()
            return {
                'message': 'Error processing attendance', 
                'error': str(e)
            }, 500

class AttendanceSummaryResource(Resource):
    """
    Resource for retrieving attendance summaries.
    """
    @jwt_required()
    def get(self):
        """
        Get attendance summary for the current user.
        """
        current_user_id = get_jwt_identity()
        
        # Get attendance records for the current month
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        monthly_attendance = Attendance.query.filter(
            Attendance.employee_id == current_user_id,
            db.extract('month', Attendance.date) == current_month,
            db.extract('year', Attendance.date) == current_year
        ).all()
        
        summary = {
            'total_days': len(monthly_attendance),
            'present_days': len([a for a in monthly_attendance if a.status == 'Completed']),
            'attendance_records': [record.to_dict() for record in monthly_attendance]
        }
        
        return summary, 200