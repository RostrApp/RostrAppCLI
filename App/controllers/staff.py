from App.models import Shift
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

def view_shifts(staff_id, schedule_id):
    """
     Shows only the current staff member's shifts for a given schedule
     fixed:
        - Include schedule_id in filter (was showing ALL the staff’s shifts)
    """
    
    staff = get_user(staff_id)
    
    if not staff or staff.role.lower() != "staff":
        raise PermissionError("Only staff can view their shifts")

    shifts = Shift.query.filter_by(
        staff_id=staff_id,
        schedule_id=schedule_id   # <-- FIXED
    ).order_by(Shift.start_time).all()
    
    return [s.get_json() for s in shifts]


def view_schedule(staff_id, schedule_id):
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
    """
    Staff clocks in to a shift
    fixed:
        - Prevent clock-in if already clocked in.
    """
    staff = get_user(staff_id)
    if not staff or staff.role.lower() != "staff":
        raise PermissionError("Only staff can clock in")
    
    shift = Shift.get_shift(shift_id)

    if not shift or shift.staff_id != staff_id:
        raise ValueError("Invalid shift for staff")
    
    # --- FIX: prevent double clock-in ---
    if shift.clock_in is not None:
        raise ValueError("Staff member has already clocked in for this shift")

    shift.clock_in = datetime.now()
    shift.updateStatus()     #automatically updates the status for the clock in
    db.session.commit()
    return shift


def clock_out(staff_id, shift_id):
    """ 
    Staff clocks out of a shift
    fixed:
        - Prevent clock-out if not clocked in yet.  
    """
    staff = get_user(staff_id)
    if not staff or staff.role.lower() != "staff":
        raise PermissionError("Only staff can clock out")

    shift = Shift.get_shift(shift_id)

    if not shift or shift.staff_id != staff_id:
        raise ValueError("Invalid shift for staff")
    
     # --- FIX: prevent clock-out before clock-in ---
    if shift.clock_in is None:
        raise ValueError("Cannot clock out before clocking in")
    
    # Prevent double clock-out
    if shift.clock_out is not None:
        raise ValueError("Staff member has already clocked out for this shift")

    shift.clock_out = datetime.now()
    shift.updateStatus()     #automatically updates the status for the clock out
    db.session.commit()
    
    return shift