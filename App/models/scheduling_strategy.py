from abc import ABC, abstractmethod
from App.controllers.user import get_all_users_by_role, get_all_shifts

class SchedulingStrategy(ABC):
    
    # gets updated list from db upon initialization
    def __init__(self):
        super().__init__()
        self.all_staff = get_all_users_by_role("staff")
        self.shifts = get_all_shifts()

    @abstractmethod
    def schedule_shift(self):
        #return Schedule object in concrete classes
        pass