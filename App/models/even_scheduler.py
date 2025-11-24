from App.models.schedule import Schedule
from App.models.scheduling_strategy import SchedulingStrategy

class EvenScheduler(SchedulingStrategy):

    def schedule_shift(self, staff, shifts, admin_id):
        """
        Assign shifts evenly across staff.
        Returns a Schedule object with shifts assigned.
        """

        # Compute schedule bounds
        start_date = min(s.start_time for s in shifts)
        end_date = max(s.end_time for s in shifts)

        # Create schedule with new constructor
        schedule = Schedule(start_date=start_date, end_date=end_date, admin_id=admin_id)

        # Assign staff in round-robin fashion
        for i, shift in enumerate(shifts):
            shift.staff_id = staff[i % len(staff)].id
            schedule.shifts.append(shift)

        return schedule
