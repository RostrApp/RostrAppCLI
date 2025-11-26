from App.database import db
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Enum

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String, default="Scheduled")

    staff = db.relationship("Staff", backref="shifts", foreign_keys=[staff_id])

    @classmethod
    def get_shift(cls, shift_id):
        return db.session.get(cls, shift_id)
    
    def assignStaff(self, staff):
        # Links a staff obj to this Shift
        # Updates staff_id and relationship
        
        self.staff = staff
        self.staff_id = staff.id
        db.session.commit()
        
        
    def getHours(self):
        # Calculate hours worked using clock-in and clock-out times
        # Returns float (hours). Returns 0 if not completed
        
        if not self.clock_in or not self.clock_out:
            return 0.0
        
        duration = self.clock_out - self.clock_in
        hours = duration.total_seconds() / 3600
        return round(hours, 2)    
        
        
    def updateStatus(self):
        # Update shift status based on timing and presence of clock-in/out.
        
        now = datetime.now()

        # Completed -> has both clock-in and clock-out
        if self.clock_in and self.clock_out:
            self.status = "Completed"

        # Ongoing -> clocked in but not out yet
        elif self.clock_in and not self.clock_out:
            self.status = "Ongoing"

        # Late -> start_time passed, but staff hasn't clocked in, but clock-in still possible
        elif now > self.start_time and not self.clock_in and now < self.end_time:
            self.status = "Late"

        # Missed -> end_time passed and no clock-in
        elif now > self.end_time and not self.clock_in:
            self.status = "Missed"

        # Scheduled -> future shift not yet started
        elif now < self.start_time:
            self.status = "Scheduled"

        db.session.commit()   
        
        def get_json(self):
            return {
                "id": self.id,
                "schedule_id": self.schedule_id,
                "end_time": self.end_time.isoformat(),
                "clock_in": self.clock_in.isoformat() if self.clock_in else None,
                "clock_out": self.clock_out.isoformat() if self.clock_out else None,
                "status": self.status
            }    