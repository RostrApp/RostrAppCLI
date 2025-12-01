from App.controllers.report import get_summary
from App.models.report import Report
from datetime import datetime

def generate_report(scheduleID, adminID):
    """
    Generate a Report object for a given schedule.
    Calls get_summary() from report controller and formats the result.
    """
    summary_dict = get_summary(scheduleID)

    report = Report(
        #schedule_id=scheduleID,
        admin_id=adminID,
        generated_date=datetime.now(),#added this
        summary=summary_dict.get("summary", "")
    )

    return report
