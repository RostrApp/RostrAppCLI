from datetime import datetime
from App.models.schedule import Schedule
from App.models.scheduling_strategy import SchedulingStrategy

class DayNightScheduler(SchedulingStrategy):

    def schedule_shift(self, staff, shifts, admin_id):
        """
        Assigns day shifts to the first staff member and night shifts to the second.
        Returns a Schedule object with shifts assigned.
        """

        # Compute overall schedule bounds
        start_date = min(s.start_time for s in shifts)
        end_date = max(s.end_time for s in shifts)

        # Create the schedule with new constructor
        schedule = Schedule(start_date=start_date, end_date=end_date, admin_id=admin_id)

        # Simple assumption: staff[0] = day staff, staff[1] = night staff
        for shift in shifts:
            if shift.start_time.hour < 18:   # before 6pm = day
                shift.staff_id = staff[0].id
            else:                            # 6pm or later = night
                shift.staff_id = staff[1].id
            schedule.shifts.append(shift)

        return schedule
