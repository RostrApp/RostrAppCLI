from App.models.schedule import Schedule


# This controller summarises the attendance of staff for a given schedule
def get_summary(scheduleID):
    schedule = Schedule.query.get(scheduleID)
    if not schedule:
        raise ValueError("Schedule not found")

    days = {}
    for shift in schedule.shifts:
        day = shift.start_time.strftime("%Y-%m-%d")

        if day not in days:
            days[day] = {
                "scheduled": set(),
                "completed": set(),
                "late": set(),
                "missed": set(),
                "ongoing": set(),
            }

        staff = shift.staff
        days[day]["scheduled"].add(staff.username)

        status = shift.status
        
        if status == ShiftStatus.SCH:
            days[day]["scheduled"].add(staff.username)
        elif status == ShiftStatus.COM:
            days[day]["completed"].add(staff.username)
        elif status == ShiftStatus.LAT:
            days[day]["late"].add(staff.username)
        elif status == ShiftStatus.MIS:
            days[day]["missed"].add(staff.username)
        elif status == ShiftStatus.ONG:
            days[day]["ongoing"].add(staff.username)

    # Convert sets to lists
    for day, record in days.items():
        for key in record:
            record[key] = list(record[key])

    return {"schedule_id": schedule.id, "days": days}
