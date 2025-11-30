from App.services.scheduling_strategy import SchedulingStrategy
from App.models.shift import Shift
from datetime import timedelta

class MinimumScheduler(SchedulingStrategy):
    def fill_schedule(self, staff_list, schedule):
        """
        Generate shifts between schedule.start_date and schedule.end_date,
        assign all shifts to the first staff member, and append them to the schedule.
        """

        current_day = schedule.start_date
        end_day = schedule.end_date

        while current_day <= end_day:
            # Example: one shift per day, 9am–5pm
            shift = Shift(
                start_time=current_day.replace(hour=9, minute=0),
                end_time=current_day.replace(hour=17, minute=0),
                staff_id=staff_list[0].id,
                schedule_id=schedule.id
            )
            schedule.shifts.append(shift)
            current_day += timedelta(days=1)