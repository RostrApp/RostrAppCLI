from App.services import scheduling_strategy

class Scheduler():
    # class diagram uses composition so I assume Scheduler class should be 
    # initialized with a strategy
    def __init__(self, strategy):
        self.setStrategy(strategy)

    def set_strategy(self, strategy):
        self.strategy = strategy
    
    def fill_schedule(self, staff, schedule):
        self.strategy.fill_schedule()