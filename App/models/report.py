from App.database import db


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    generated_date = db.Column(db.DateTime, nullable=False)
    summary = db.Column(db.JSON, nullable=False)

    admin = db.relationship("Admin", backref="reports", foreign_keys=[admin_id])

    def get_json(self):
        return {
            "admin_id": self.admin_id,
            "admin_name": self.admin.username,
            "generated_date": self.generated_date.isoformat()
        }

    def __init__(self, admin_id, generated_date, summary):
        self.id = id
        self.admin_id = admin_id
        self.generated_date = generated_date
        self.summary = summary