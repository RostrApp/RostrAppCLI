from App.database import db
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Enum

class ShiftStatus(PyEnum):
    SCH = "scheduled"
    COM = "completed"
    MIS = "missed"
    CAN = "cancelled"
    ONG = "ongoing"

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        Enum(ShiftStatus, name="shift_status_enum"),
        default=ShiftStatus.SCH,
        nullable=False
    )

    
    staff = db.relationship("Staff", backref="shifts", foreign_keys=[staff_id])

    def get_json(self):
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "staff_name": self.staff.username if self.staff else None,
            "start_time": self.start_time.isoformat(),
            "schedule_id": self.schedule_id,
            "end_time": self.end_time.isoformat(),
            "clock_in": self.clock_in.isoformat() if self.clock_in else None,
            "clock_out": self.clock_out.isoformat() if self.clock_out else None
        }

    def __init__(self, staff_id, schedule_id, start_time, end_time):
         self.staff_id = staff_id
         self.schedule_id = schedule_id
         self.start_time = start_time
         self.end_time = end_time

    def assign_staff(self, staff):
         self.staff_id = staff.id

    def update_status(self, status):
         self.status = status