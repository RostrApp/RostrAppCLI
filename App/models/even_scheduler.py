# Task 9: EvenScheduler class implementation
from App.models.scheduling_strategy import SchedulingStrategy
from App.models.schedule import Schedule

class EvenScheduler(SchedulingStrategy):

    def schedule_shift(self, staff_list, shift_list, creator_id):
        schedule = Schedule(
            name="Even Schedule",
            created_by=creator_id
        )

        staff_count = len(staff_list)
        i = 0

        for shift in shift_list:
            assigned_staff = staff_list[i % staff_count]
            shift.staff_id = assigned_staff.id
            schedule.shifts.append(shift)
            i += 1

        return schedule
