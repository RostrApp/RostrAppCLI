from App.services.scheduling_strategy import SchedulingStrategy
from App.models.shift import Shift
from datetime import timedelta

class DayNightScheduler(SchedulingStrategy):
    def fill_schedule(self, staff_list, schedule):
        """
        Generate shifts between schedule.startDate and schedule.endDate,
        assign day shifts to staff_list[0], night shifts to staff_list[1],
        and append them to the schedule.
        """

        current_day = schedule.start_date
        end_day = schedule.end_date

        while current_day <= end_day:
            day_shift = Shift(
                start_time=current_day.replace(hour=8, minute=0),
                end_time=current_day.replace(hour=16, minute=0),
                staff_id=staff_list[0].id,
                schedule_id=schedule.id
            )
            schedule.shifts.append(day_shift)

            night_shift = Shift(
                start_time=current_day.replace(hour=18, minute=0),
                end_time=(current_day + timedelta(days=1)).replace(hour=0, minute=0),
                staff_id=staff_list[1].id,
                schedule_id=schedule.id
            )
            schedule.shifts.append(night_shift)

            current_day += timedelta(days=1)