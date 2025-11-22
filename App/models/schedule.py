from datetime import datetime
from App.database import db

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False) # not necessary if auto-populated by scheduler
    shifts = db.relationship("Shift", backref="schedule", lazy=True)
    scheduling_strategy = db.Column(db.String(50), nullable=True)  # e.g., "Even", "Minimum", etc.

    def shift_count(self):
        return len(self.shifts)

    def get_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "shift_count": self.shift_count(),
            "shifts": [shift.get_json() for shift in self.shifts]
        }
    
    
    
        # according to the test plan, this class is created when
        # staff members are assigned to shifts (i.e. timeslots)  
        # and these assignments are added to the schedule.

        # should be created by appropriate Scheduler upon refactor


