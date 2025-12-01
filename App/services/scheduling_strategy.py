from abc import ABC, abstractmethod
from App.models.staff import Staff
from App.models.schedule import Schedule
from App.controllers.user import get_all_users_by_role, get_all_shifts

class SchedulingStrategy(ABC):
    @abstractmethod
    def __init__(self):
        super().__init__()

    # or just get list of staff and shifts from db upon initializing
    '''
    def __init__(self):
        super().__init__()
        self.all_staff = get_all_users_by_role("staff")
        self.shifts = get_all_shifts()
    '''
    

    @abstractmethod
    def fill_schedule(self, staff_list, schedule):
        #return Schedule object in concrete classes
        pass