# Task 9: EvenScheduler class implementation
from App.models.scheduling_strategy import SchedulingStrategy
from App.models.schedule import Schedule

class MinimumScheduler(SchedulingStrategy):

    def schedule_shift(self, staff_list, shift_list, creator_id):
        schedule = Schedule(
            name="Minimum Day Schedule",
            created_by=creator_id
        )

        # simple: always assign first staff (placeholder)
        primary = staff_list[0]

        for shift in shift_list:
            shift.staff_id = primary.id
            schedule.shifts.append(shift)

        return schedule
