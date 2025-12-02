from App.models import Shift, Schedule
from App.database import db
from App.controllers.user import get_user
from App.controllers.schedule import generate_report

#create an empty schedule with start and end date
def create_schedule(start_date, end_date, admin_id):
    admin = get_user(admin_id)
    
    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can create schedules")
        
    new_schedule = Schedule(start_date, end_date, admin_id)
    
    db.session.add(new_schedule)
    db.session.commit()
    return new_schedule

#assign all staff to a weekly schedule using a scheduler
from App.services.scheduler import Scheduler

def schedule_week(strategy, schedule_id, staff_list, admin_id):
    admin = get_user(admin_id)

    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can create schedules")

    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        raise ValueError("Invalid schedule ID")

    valid_staff = []
    for staff_id in staff_list:
        staff = get_user(staff_id)
        if staff and staff.role == "staff":
            valid_staff.append(staff)
        else:
            print(f"Skipping invalid staff ID: {staff_id}")

    if not valid_staff:
        raise ValueError("No valid staff members to schedule")

    # ✅ Use Scheduler wrapper instead of calling strategy directly
    scheduler = Scheduler(strategy)
    scheduler.fill_schedule(valid_staff, schedule)

    db.session.commit()
    return schedule

    

#create a shift and add it to a schedule
def schedule_shift(schedule_id, start_time, end_time, staff_id, admin_id):
    admin = get_user(admin_id)
    staff = get_user(staff_id)
    schedule = db.session.get(Schedule, schedule_id)

    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can schedule shifts")
    if not staff or staff.role != "staff":
        raise ValueError("Invalid staff member")
    if not schedule:
        raise ValueError("Invalid schedule ID")

    new_shift = Shift(
        staff_id=staff_id,
        schedule_id=schedule_id,
        start_time=start_time,
        end_time=end_time
    )

    db.session.add(new_shift)
    db.session.commit()

    return new_shift

#view the shift report for a given schedule
def view_report(schedule_id, admin_id):
    admin = get_user(admin_id)
    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can view shift reports")

    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        raise ValueError("Invalid schedule ID")

    return generate_report(schedule_id, admin_id)