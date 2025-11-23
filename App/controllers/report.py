# This controller summarises the attendance of staff for a given schedule
def get_summary(scheduleID):
    schedule = Schedule.query.get(scheduleID)
    if not schedule:
       raise ValueError("Schedule not found")

    days = {}
    for shifts in schedule.shifts:
        if day not in days:
          days[day] = {
              "assigned": set(),
              "present": set(),
              "late": set(),
              "missed": set(),
          }
  
        staff = shift.staff
  
        # Add assigned staff
        days[day]["assigned"].add(staff)
  
        # Record staff's attendance
        if shift.clock_in:
            days[day]["present"].add(staff)
            if shift.clock_in > shift.start_time:
                days[day]["late"].add(staff)
        else:
            days[day]["missed"].add(staff)
  
        # Convert sets to lists
        for day, record in days.items():
            for key in record:
              record[key] = list(record[key])
  
        return {
            "schedule_id": schedule.id,
            "days": days
        }
      
    