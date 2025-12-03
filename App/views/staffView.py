# app/views/staff_views.py
from flask import Blueprint, jsonify, request
from App.controllers import staff
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

staff_views = Blueprint('staff_views', __name__, template_folder='../templates')

# Refactored staff views 

staff_views = Blueprint('staff_views', __name__, template_folder='../templates')

# Staff view schedule roster route (calls view_schedule)
# GET /staff/schedule/<schedule_id>

@staff_views.route('/staff/schedule/<int:schedule_id>', methods=['GET'])
@jwt_required()
def view_schedule(schedule_id):
    try:
        staff_id = int(get_jwt_identity())
        roster = staff.view_schedule(staff_id, schedule_id)
        return jsonify(roster), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500


# Staff view shifts for a schedule route (calls view_shifts)
# GET /staff/shifts/<schedule_id>

@staff_views.route('/staff/shifts/<int:schedule_id>', methods=['GET'])
@jwt_required()
def view_shifts(schedule_id):
    try:
        staff_id = int(get_jwt_identity())
        shifts = staff.view_shifts(staff_id, schedule_id)
        return jsonify(shifts), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500


# View a specific shift
# GET /staff/shift/<shift_id>

@staff_views.route('/staff/shift/<int:shift_id>', methods=['GET'])
@jwt_required()
def view_shift(shift_id):
    try:
        shift = staff.Shift.get_shift(shift_id)
        if not shift:
            return jsonify({"error": "Shift not found"}), 404
        return jsonify(shift.get_json()), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500



# Staff Clock In
# POST /staff/clock_in/shift_id

@staff_views.route('/staff/clock_in/<int:shift_id>', methods=['POST'])
@jwt_required()
def clock_in_view(shift_id):
    try:
        staff_id = int(get_jwt_identity())# db uses int for userID so we must convert
        shift = staff.clock_in(staff_id, shift_id)  # Call controller
        return jsonify(shift.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500



# Staff Clock Out
# POST /staff/clock_out/shift_id

@staff_views.route('/staff/clock_out/<int:shift_id>', methods=['POST'])
@jwt_required()
def clock_out_view(shift_id):
    try:
        staff_id = int(get_jwt_identity()) # db uses int for userID so we must convert
        shift = staff.clock_out(staff_id, shift_id)  # Call controller
        return jsonify(shift.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500