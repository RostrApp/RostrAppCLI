from abc import ABC, abstractmethod

class SchedulingStrategy(ABC):
    """
    Abstract base class for scheduling strategies.
    Concrete classes must implement schedule_shift(staff, shifts, admin_id).
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def schedule_shift(self, staff, shifts, admin_id):
        """
        Assign staff to shifts and return a Schedule object.
        """
        pass
