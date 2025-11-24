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
                "assigned": set(),
                "present": set(),
                "late": set(),
                "missed": set(),
            }

        staff = shift.staff

        # Add assigned staff
        days[day]["assigned"].add(staff.username)

        # Record staff's attendance
        if shift.clock_in:
            days[day]["present"].add(staff.username)
            if shift.clock_in > shift.start_time:
                days[day]["late"].add(staff.username)
        else:
            days[day]["missed"].add(staff.username)

    # Convert sets to lists
    for day, record in days.items():
        for key in record:
            record[key] = list(record[key])

    return {"schedule_id": schedule.id, "days": days}
