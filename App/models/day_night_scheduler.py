# Task 9: DayNightScheduler class implementation
from App.models.scheduling_strategy import SchedulingStrategy
from App.models.schedule import Schedule

class DayNightScheduler(SchedulingStrategy):

    def schedule_shift(self, staff_list, shift_list, creator_id):
        schedule = Schedule(
            name="Day Night Schedule",
            created_by=creator_id
        )

        if len(staff_list) < 2:
            raise Exception("Need at least 2 staff for day/night scheduling")

        day_staff = staff_list[0]
        night_staff = staff_list[1]

        for shift in shift_list:
            if shift.start_time.hour < 18:
                shift.staff_id = day_staff.id
            else:
                shift.staff_id = night_staff.id
            schedule.shifts.append(shift)

        return schedule
