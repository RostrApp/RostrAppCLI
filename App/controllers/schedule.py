from App.controllers.report import get_summary
from App.models.report import Report
from datetime import datetime
from App.database import db
from App.models.user import User

def generate_report(scheduleID, adminID):
    """
    Generate a Report object for a given schedule.
    Calls get_summary() from report controller and formats the result.
    """

    user = db.session.get(User, adminID)
    if not user or user.role.lower() != "admin":
        raise PermissionError("Only admins can generate shift reports")
                              
    summary_dict = get_summary(scheduleID)

    report = Report(
        #schedule_id=scheduleID,
        admin_id=adminID,
        generated_date=datetime.now(),#added this
        summary=summary_dict
    )

    return report
