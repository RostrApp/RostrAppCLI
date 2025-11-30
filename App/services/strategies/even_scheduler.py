from App.services.scheduling_strategy import SchedulingStrategy
from App.models.shift import Shift
from datetime import timedelta

class EvenScheduler(SchedulingStrategy):
    def fill_schedule(self, staff_list, schedule):
        """
        Generate shifts between schedule.start_date and schedule.end_date,
        assign them evenly across staff_list, and append each shift to the schedule.
        """

        current_day = schedule.start_date
        end_day = schedule.end_date
        staff_count = len(staff_list)
        shift_index = 0

        while current_day <= end_day:
            
            shift = Shift(
                start_time=current_day.replace(hour=9, minute=0),
                end_time=current_day.replace(hour=17, minute=0),
                staff_id=staff_list[shift_index % staff_count].id,
                schedule_id=schedule.id
            )
            schedule.shifts.append(shift)
            shift_index += 1
            current_day += timedelta(days=1)