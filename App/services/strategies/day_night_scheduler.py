from App.models.staff import Staff
from App.models.schedule import Schedule
from App.controllers.user import get_all_users_by_role, get_all_shifts
from App.services.scheduling_strategy import SchedulingStrategy 

class DayNightScheduler(SchedulingStrategy):

    def fill_schedule(self, staff, schedule):
        # return Schedule object -> create_day_night_schedule(self.all_staff, self.shifts)
        # this method will be in Schedule controller
        pass