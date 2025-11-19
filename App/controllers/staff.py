from App.models import Shift
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

def viewShifts(staff_id):
    # Shows only the current staff member's shifts for a given schedule
    
    staff = get_user(staff_id)
    
    if not staff or staff.role.lower() != "staff":
        raise PermissionError("Only staff can view their shifts")

    shifts = Shift.query.filter_by(
        staff_id=staff_id
    ).order_by(Shift.start_time).all()

    return [s.get_json() for s in shifts]


def viewSchedule(staff_id, schedule_id):
    # Combined view of all shifts in a schedule for staff members
    # Replaces get_combined_roster()
    
    staff = get_user(staff_id)
    
    if not staff or staff.role.lower() != "staff":
        raise PermissionError("Only staff can view schedule rosters")

    shifts = Shift.query.filter_by(
        schedule_id=schedule_id
    ).order_by(Shift.start_time).all()

    return [s.get_json() for s in shifts]


def clock_in(staff_id, shift_id):
    staff = get_user(staff_id)
    
    if not staff or staff.role.lower() != "staff":
        raise PermissionError("Only staff can clock in")

    shift = Shift.get_shift(shift_id)

    if not shift or shift.staff_id != staff_id:
        raise ValueError("Invalid shift for staff")

    shift.clock_in = datetime.now()
    shift.updateStatus()     #automatically updates the status for the clock in
    db.session.commit()
    return shift


def clock_out(staff_id, shift_id):
    staff = get_user(staff_id)
    
    if not staff or staff.role != "staff":
        raise PermissionError("Only staff can clock out")

    shift = Shift.get_shift(shift_id)

    if not shift or shift.staff_id != staff_id:
        raise ValueError("Invalid shift for staff")

    shift.clock_out = datetime.now()
    shift.updateStatus()     #automatically updates the status for the clock out
    db.session.commit()
    return shift