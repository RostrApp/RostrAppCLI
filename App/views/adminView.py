# app/views/staff_views.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta, date
from App.controllers import staff, auth, admin
from App.controllers.user import get_all_users_by_role
from App.services.strategies.day_night_scheduler import DayNightScheduler
from App.services.strategies.even_scheduler import EvenScheduler
from App.services.strategies.minimum_scheduler import MinimumScheduler
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

admin_view = Blueprint('admin_views', __name__, template_folder='../templates')

# Admin authentication decorator
# def admin_required(fn):
#     @jwt_required()
#     def wrapper(*args, **kwargs):
#         user_id = get_jwt_identity()
#         user = auth.get_user(user_id)
#         if not user or not user.is_admin:
#             return jsonify({"error": "Admin access required"}), 403
#         return fn(*args, **kwargs)
#     return wrapper
# Based on the controllers in App/controllers/admin.py, admins can do the following actions:
# 1. Create Schedule
# 2. Get Schedule Report

@admin_view.route('/createSchedule', methods=['POST'])
@jwt_required()
def createSchedule():
    try:
        admin_id = int(get_jwt_identity())
        data = request.get_json()

        '''
        body of request should be in the format
        {
            "start_date": "30-11-2025",
            "end_date": "06-12-2025"
        }
        '''
        
        start_date_string = data["start_date"] # will throw KeyError for bad request body
        end_date_string = data["end_date"]


        start_date = datetime.strptime(start_date_string, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_string, "%Y-%m-%d")
        schedule = admin.create_schedule(start_date, end_date, admin_id)  
        return jsonify(schedule.get_json()), 200 
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError as e:
        return jsonify({"error": f'Database error: "{e}"'}), 500
    except KeyError as e:
        return jsonify({"error": f'"{e}" is required for schedule creation'}), 400

@admin_view.route('/scheduleWeek', methods=['POST'])
@jwt_required()
def scheduleWeek():
    try:
        admin_id = int(get_jwt_identity())
        data = request.get_json()
        staff = get_all_users_by_role("staff")
        staff_list = []
        for user in staff:
            staff_list.append(user.id)

        '''
        body of request should be in the format
        {
            "strategy": "schedulingStrategy",
            "scheduleId": id
        }
        '''
       
        strategy_string = data["strategy"] # will throw KeyError for bad request body
        if strategy_string == "day_night_scheduler":
            strategy = DayNightScheduler()
        elif strategy_string == "even_scheduler":
            strategy = EvenScheduler()
        elif strategy_string == "minimum_scheduler":
            strategy = MinimumScheduler()
        else:
            raise ValueError("Invalid strategy type")
        
        schedule_id = int(data["scheduleId"])
        schedule = admin.schedule_week(strategy, schedule_id, staff_list, admin_id)  
        return jsonify(schedule.get_json()), 200 
    except (PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError as e:
        return jsonify({"error": f'Database error: "{e}"'}), 500
    except KeyError as e:
        return jsonify({"error": f'"{e}" is required for schedule creation'}), 400
    except ValueError as e:
        return jsonify({"error": f'{e}'}), 400
    

@admin_view.route('/scheduleShift', methods=['POST'])
@jwt_required()
def scheduleShift():
    try:
        admin_id = get_jwt_identity()

        '''
        body of request should be in the format
        {
            "scheduleId": id,
            "staffId": id,
            "startTime": "2025-12-04 09:00:00"
            "endTime": "2025-12-04 17:00:00"
        }
        '''

        data = request.get_json()
        schedule_id = int(data["scheduleId"])
        staff_id = int(data["staffId"])
        start_time_string = data["startTime"]
        end_time_string = data["endTime"] 

        # Try ISO first, fallback to "YYYY-MM-DD HH:MM:SS"
        try:
            start_time = datetime.fromisoformat(start_time_string)
            end_time = datetime.fromisoformat(end_time_string)
        except ValueError:
            start_time = datetime.strptime(start_time_string, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(end_time_string, "%Y-%m-%d %H:%M:%S")

        shift = admin.schedule_shift(schedule_id, start_time, end_time, staff_id, admin_id)  # Call controller method
        return jsonify(shift.get_json()), 200 # Return the created shift as JSON
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500
    except KeyError as e:
        return jsonify({"error": f'"{e}" is required for shift creation'}), 400

@admin_view.route('/viewReport/<int:schedule_id>', methods=['GET'])
@jwt_required()
def viewReport(schedule_id):
    try:
        admin_id = get_jwt_identity()
        report = admin.view_report(schedule_id, admin_id) 
        return report.get_json(), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500
    except KeyError as e:
        return jsonify({"error": f'"{e}" is required to view report'}), 400