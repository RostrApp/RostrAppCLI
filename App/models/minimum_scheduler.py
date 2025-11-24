from App.models.schedule import Schedule
from App.models.scheduling_strategy import SchedulingStrategy

class MinimumScheduler(SchedulingStrategy):

    def schedule_shift(self, staff, shifts, admin_id):
        """
        Assign all shifts to the first staff member.
        Returns a Schedule object with shifts assigned.
        """

        # Compute schedule bounds
        start_date = min(s.start_time for s in shifts)
        end_date = max(s.end_time for s in shifts)

        # Create schedule with new constructor
        schedule = Schedule(start_date=start_date, end_date=end_date, admin_id=admin_id)

        # Assign every shift to the first staff member
        for shift in shifts:
            shift.staff_id = staff[0].id
            schedule.shifts.append(shift)

        return schedule
