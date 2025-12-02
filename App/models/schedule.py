from datetime import datetime
from App.database import db

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    #shifts = db.relationship("Shift", backref="schedule", lazy=True)
    shifts = db.relationship("Shift", back_populates="schedule", cascade="all, delete-orphan")

    def get_json(self):
        return {
            "id": self.id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "admin_id": self.admin_id,
        }

    def __init__(self, start_date, end_date, admin_id):
         self.start_date = start_date
         self.end_date = end_date
         self.admin_id = admin_id

    def get_shifts(self):
         return self.shifts

    def add_shift(self, shift):
        shift.schedule = self
        return self

    def remove_shift(self, shift):
        shift.schedule = None
        return self
    