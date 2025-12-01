from App.database import db
from .user import User

class Staff(User):
    #id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "staff",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "staff")
