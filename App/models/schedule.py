from datetime import datetime
from App.database import db

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    shifts = db.relationship("Shift", backref="schedule", lazy=True)

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


