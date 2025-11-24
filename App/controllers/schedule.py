from datetime import datetime
from App.models.schedule import Schedule

def create_even_schedule(all_staff, shifts, admin_id):
    """
    Assign shifts evenly across staff.
    """
    start_date = min(s.start_time for s in shifts)
    end_date = max(s.end_time for s in shifts)
    schedule = Schedule(start_date=start_date, end_date=end_date, admin_id=admin_id)

    for i, shift in enumerate(shifts):
        shift.staff_id = all_staff[i % len(all_staff)].id
        schedule.shifts.append(shift)

    return schedule


def create_minimum_schedule(all_staff, shifts, admin_id):
    """
    Assign all shifts to the first staff member.
    """
    start_date = min(s.start_time for s in shifts)
    end_date = max(s.end_time for s in shifts)
    schedule = Schedule(start_date=start_date, end_date=end_date, admin_id=admin_id)

    for shift in shifts:
        shift.staff_id = all_staff[0].id
        schedule.shifts.append(shift)

    return schedule


def create_day_night_schedule(all_staff, shifts, admin_id):
    """
    Assign day shifts to the first staff member and night shifts to the second.
    """
    start_date = min(s.start_time for s in shifts)
    end_date = max(s.end_time for s in shifts)
    schedule = Schedule(start_date=start_date, end_date=end_date, admin_id=admin_id)

    for shift in shifts:
        if shift.start_time.hour < 18:  # before 6pm = day
            shift.staff_id = all_staff[0].id
        else:                           # 6pm or later = night
            shift.staff_id = all_staff[1].id
        schedule.shifts.append(shift)

    return schedule
