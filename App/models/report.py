from App.database import db

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    generated_date = db.Column(db.DateTime, nullable=False)

    admin = db.relationship("Admin", backref="reports", foreign_keys=[admin_id])

    def get_json(self):
      return {
          "id": self.id,
          "admin_id": self.admin_id,
          "admin_name": self.admin.username,
          "generated_date": self.generated_date.isoformat()
      }

    def __init__(self, admin_id, generated_date):
       self.id = id
       self.admin_id = admin_id
       self.generated_date = generated_date
      
      
      