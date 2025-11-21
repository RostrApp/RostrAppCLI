from App.controllers.user import get_all_users_by_role, get_all_shifts
from App.models.schedule import Schedule
from App.models.even_scheduler import EvenScheduler
from App.models.minimum_scheduler import MinimumScheduler
from App.models.day_night_scheduler import DayNightScheduler

def create_even_schedule(all_staff, shifts, creator_id):
    scheduler = EvenScheduler()
    return scheduler.schedule_shift(all_staff, shifts, creator_id)


def create_minimum_schedule(all_staff, shifts, creator_id):
    scheduler = MinimumScheduler()
    return scheduler.schedule_shift(all_staff, shifts, creator_id)

def create_day_night_schedule(all_staff, shifts, creator_id):
    scheduler = DayNightScheduler()
    return scheduler.schedule_shift(all_staff, shifts, creator_id)