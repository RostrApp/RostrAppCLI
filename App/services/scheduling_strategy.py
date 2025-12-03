from abc import ABC, abstractmethod

class SchedulingStrategy(ABC):
    #@abstractmethod
    def __init__(self):
        super().__init__()    

    @abstractmethod
    def fill_schedule(self, staff_list, schedule):
        #return Schedule object in concrete classes
        pass