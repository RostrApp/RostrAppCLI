# import os, tempfile, pytest, logging, unittest, datetime
# from werkzeug.security import check_password_hash, generate_password_hash
# from App.main import create_app
# from App.database import db, create_db
# from datetime import datetime, timedelta, date
# from App.models import User, Schedule, Shift, Staff, Report
# from App.services.strategies.minimum_scheduler import MinimumScheduler
# from App.controllers import (
#     create_user,
#     create_schedule,
#     schedule_shift, 
#     schedule_week,
#     view_report,
#     view_schedule,
#     view_shifts,
#     clock_in,
#     clock_out, 
#     get_summary
# )

# LOGGER = logging.getLogger(__name__)
# '''
#    Unit Tests
# '''

# class UserUnitTests(unittest.TestCase):

    # def test_new_user(self):
    #     user = User("john", "johnpass", "staff")
    #     assert user.id == 1

#     def test_new_user_invalid_role(self):
#         user = User("jim", "jimpass", "ceo")
#         assert user is None

#     def test_get_json(self):
#         user = User("bob", "bobpass", "admin")
#         user_json = user.get_json()
#         assert user_json["username"] == "bob"
#         assert user_json["role"] == "admin"

#     def test_hashed_password(self):
#         password = "mypass"
#         user = User(username="tester", password=password)
#         assert user.password != password
#         assert user.check_password(password) == True

#     def test_check_password(self):
#         password = "mypass"
#         user = User("bob", password)
#         assert user.check_password(password) == True


# # Admin unit tests
# class AdminUnitTests(unittest.TestCase):
    
#     def setUp(self):                # can reuse this code since none of it is being tested for Admin tests
#         app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
#         app.app_context().push()
#         db.drop_all()
#         db.create_all()

#         self.admin = create_user("admin", "adminpass", "admin")
#         self.staff1 = create_user("staff1", "staffpass", "staff")
#         self.staff2 = create_user("staff2", "staffpass", "staff")
#         self.staff3 = create_user("staff3", "staffpass", "staff")
#         self.staff_list = [self.staff1.id, self.staff2.id, self.staff3.id]
#         db.session.add_all([self.admin, self.staff1, self.staff2, self.staff3])
#         db.session.commit()

#         self.start_time = datetime.now()
#         self.end_time = self.start_time + timedelta(hours=8)
#         self.start_date = date.today()
#         self.end_date = self.start_date + timedelta(days=6)


#     def test_create_schedule(self):
#         schedule = create_schedule(self.start_date, self.end_date, self.admin.id)
#         db.session.add(schedule)
#         db.session.commit()
#         assert schedule

#     def test_create_schedule_invalid_role(self):
#         with pytest.raises(PermissionError, match="Only admins can create schedules"):
#             schedule = create_schedule(self.start_date, self.end_date, self.staff1.id)
#             assert schedule is None

#     def test_schedule_week_valid(self):        
#         schedule = Schedule(self.start_date, self.end_date, self.admin.id)
#         db.session.add(schedule)    
#         db.session.commit()

#         strategy = MinimumScheduler()
#         schedule_week(strategy, schedule.id, self.staff_list, self.admin.id)
#         shifts = schedule.get_shifts()

#         assert len(schedule.shifts) == 7    # should be 1 per day
#         assert shifts[0].staff_id == self.staff1.id
#         assert isinstance(shifts[0], Shift)

#     def test_schedule_week_invalid(self):
#         invalid_schedule_id = 999
#         strategy = MinimumScheduler()

#         with pytest.raises(ValueError, match="Invalid schedule ID"):
#             shift = schedule_week(strategy, invalid_schedule_id, self.staff_list, self.admin.id)
#             assert shift is None
    
#     def test_schedule_shift_valid(self):
#         schedule = Schedule(self.start_date, self.end_date, self.admin.id)
#         db.session.add(schedule)
#         db.session.commit()

#         shift = schedule_shift(schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)

#         assert shift.staff_id == self.staff1.id
#         assert shift.schedule_id == schedule.id
#         assert shift.start_time == self.start_time
#         assert shift.end_time == self.end_time
#         assert isinstance(shift, Shift)

#     def test_schedule_shift_invalid(self):
#         invalid_schedule_id = 999
#         with pytest.raises(ValueError, match="Invalid schedule ID"):
#             shift = schedule_shift(invalid_schedule_id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
#             assert shift is None

#     def test_view_report(self):
#         schedule = Schedule(self.start_date, self.end_date, self.admin.id)
#         db.session.add(schedule)
#         db.session.commit()

#         shift1 = schedule_shift(schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
#         shift2 = schedule_shift(schedule.id, self.start_time, self.end_time, self.staff2.id, self.admin.id)
#         db.session.add_all([shift1, shift2])
#         db.session.commit()

#         report = view_report(schedule.id, self.admin.id)
#         assert isinstance(report, Report)
#         self.assertEqual(report.summary["schedule_id"], schedule.id)
#         self.assertIn("days", report.summary)
#         assert isinstance(report.summary["days"], dict)

#     def test_view_report_invalid(self):
#         schedule = Schedule(self.start_date, self.end_date, self.admin.id)
#         db.session.add(schedule)
#         db.session.commit()

#         with pytest.raises(PermissionError, match="Only admins can view shift reports"):
#             report = view_report(schedule.id, self.staff1.id)
#             assert report is None
    
#     # Staff unit tests
# class StaffUnitTests(unittest.TestCase):
    
#     def setUp(self):            # can reuse this code since none of it is being tested for Staff tests
#         app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
#         app.app_context().push()
#         db.drop_all()
#         db.create_all()

#         self.start_time = datetime.now()
#         self.end_time = self.start_time + timedelta(hours=8)
#         self.start_date = date.today()
#         self.end_date = self.start_date + timedelta(days=6)

#         self.admin = create_user("admin", "adminpass", "admin")
#         self.staff = create_user("staff", "pass123", "staff")
#         self.schedule = Schedule(self.start_date, self.end_date, self.admin.id)
#         db.session.add_all([self.admin, self.staff, self.schedule])
#         db.session.commit()

#         self.shift = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff.id, self.admin.id)
#         db.session.add(self.shift)
#         db.session.commit()


#     def test_view_schedule_valid(self):
#         result = view_schedule(self.staff.id, self.schedule.id)
#         self.assertEqual(len(result), 1)
#         self.assertEqual(result[0]["schedule_id"], self.schedule.id)

#     def test_view_schedule_invalid_role(self):
#         with self.assertRaises(PermissionError):
#             view_schedule(self.admin.id, 1)

#     def test_view_shifts_valid(self):
#         result = view_shifts(self.staff.id, self.schedule.id)
#         self.assertEqual(len(result), 1)
#         self.assertEqual(result[0]["staff_id"], self.staff.id)
#         self.assertEqual(result[0]["schedule_id"], self.schedule.id)

#     def test_view_shifts_invalid_user(self):
#         admin = create_user("admin_view_bad", "adminpass", "admin")
#         with self.assertRaises(PermissionError):
#             view_shifts(admin.id, 1)  

#     def test_clock_in_valid(self):
#         clocked_in_shift = clock_in(self.staff.id, self.shift.id)
#         assert clocked_in_shift.clock_in is not None

#     def test_clock_in_invalid_user(self):      
#         with self.assertRaises(PermissionError):
#             clock_in(self.admin.id, self.shift.id)

#     def test_clock_in_invalid_shift(self):
#         with self.assertRaises(ValueError):
#             clock_in(self.staff.id, 999)

#     def test_clock_in_duplicate(self):      
#         with self.assertRaises(ValueError):
#             clock_in(self.staff.id, self.shift.id)
#             clock_in(self.staff.id, self.shift.id)

#     def test_clock_out_valid(self):
#         clock_in(self.staff.id, self.shift.id)
#         clocked_out_shift = clock_out(self.staff.id, self.shift.id)
#         assert clocked_out_shift.clock_out is not None
#         assert isinstance(clocked_out_shift.clock_out, datetime)

#     def test_clock_out_invalid_user(self):
#         with self.assertRaises(PermissionError):
#             clock_out(self.admin.id, self.shift.id)

#     def test_clock_out_invalid_shift(self):
#         with pytest.raises(ValueError):
#             clock_out(self.staff.id, 999)

#     def test_clock_out_duplicate(self):
#         clock_in(self.staff.id, self.shift.id)      
#         with self.assertRaises(ValueError):
#             clock_out(self.staff.id, self.shift.id)
#             clock_out(self.staff.id, self.shift.id)


# class ReportUnitTests(unittest.TestCase):
#     def setUp(self):
#         db.drop_all()
#         db.create_all()
#         self.admin = create_user("admin_summary", "pass123", "admin")
#         self.alice = create_user("Alice", "alicepass", "staff")
#         self.bob = create_user("Bob", "bobpass", "staff")
#         self.steve = create_user("Steve", "stevepass", "staff")
#         db.session.add_all([self.admin, self.alice, self.bob, self.steve])
#         db.session.commit()

#         self.schedule = Schedule(
#             start_date=datetime(2025, 11, 17, 8),
#             end_date=datetime(2025, 11, 21, 16),
#             admin_id=self.admin.id
#         )
#         db.session.add(self.schedule)
#         db.session.commit()

#         self.shift1 = Shift(staff_id=self.alice.id,
#                     schedule_id=self.schedule.id,
#                     start_time=datetime(2025, 11, 17, 8),
#                     end_time=datetime(2025, 11, 17, 16),
#                     clock_in=datetime(2025, 11, 17, 8, 5),
#                     clock_out=datetime(2025, 11, 17, 16))

#         self.shift2 = Shift(staff_id=self.bob.id,
#                     schedule_id=self.schedule.id,
#                     start_time=datetime(2025, 11, 17, 8),
#                     end_time=datetime(2025, 11, 17, 16),
#                     clock_in=datetime(2025, 11, 17, 8, 0),
#                     clock_out=datetime(2025, 11, 17, 16))

#         self.shift3 = Shift(staff_id=self.steve.id,
#                     schedule_id=self.schedule.id,
#                     start_time=datetime(2025, 11, 17, 8),
#                     end_time=datetime(2025, 11, 17, 16))

#         self.shift4 = Shift(staff_id=self.alice.id,
#                     schedule_id=self.schedule.id,
#                     start_time=datetime(2025, 11, 20, 8),
#                     end_time=datetime(2025, 11, 20, 16))

#         db.session.add_all([self.shift1, self.shift2, self.shift3, self.shift4])
#         db.session.commit()

#     def test_get_summary_invalid_schedule(self):
#         with pytest.raises(ValueError):
#             get_summary(99999)

#     def test_get_summary_completed_shift(self):
#         admin = User(username="admin_sum", password="pass", role="admin")
#         alice = User(username="alice", password="pass", role="staff")
#         db.session.add_all([admin, alice]); db.session.commit()

#         schedule = Schedule(
#             start_date=datetime(2025,11,17),
#             end_date=datetime(2025,11,18),
#             admin_id=admin.id
#         )
#         db.session.add(schedule); db.session.commit()

#         shift = schedule_shift(schedule.id, datetime(2025,11,17,8), datetime(2025,11,17,12), alice.id, admin.id)
#         shift.clock_in = datetime(2025,11,17,8)
#         shift.clock_out = datetime(2025,11,17,12)
#         shift.updateStatus()
#         db.session.commit()

#         summary = get_summary(schedule.id)
#         day_data = summary["days"]["2025-11-17"]
#         staff_user = User.query.get(shift.staff_id)
#         assert staff_user.username in day_data["completed"]

#     def test_get_summary_late_shift(self):
#         admin = User(username="admin_sum2", password="pass", role="admin")
#         bob = User(username="bob", password="pass", role="staff")
#         db.session.add_all([admin, bob]); db.session.commit()

#         schedule = Schedule(
#             start_date=datetime(2025,11,17),
#             end_date=datetime(2025,11,18),
#             admin_id=admin.id
#         )
#         db.session.add(schedule); db.session.commit()

#         start = datetime.now() - timedelta(hours=1)
#         end = datetime.now() + timedelta(hours=3)
#         shift = schedule_shift(schedule.id, start, end, bob.id, admin.id)
#         shift.updateStatus()
#         db.session.commit()

#         summary = get_summary(schedule.id)
#         day_key = start.strftime("%Y-%m-%d")
#         day_data = summary["days"][day_key]
#         staff_user = User.query.get(shift.staff_id)
#         assert staff_user.username in day_data["late"]

#     def test_get_summary_missed_shift(self):
#         admin = User(username="admin_sum3", password="pass", role="admin")
#         steve = User(username="steve", password="pass", role="staff")
#         db.session.add_all([admin, steve]); db.session.commit()

#         schedule = Schedule(
#             start_date=datetime(2025,11,17),
#             end_date=datetime(2025,11,18),
#             admin_id=admin.id
#         )
#         db.session.add(schedule); db.session.commit()

#         shift = schedule_shift(schedule.id, datetime(2025,11,17,8), datetime(2025,11,17,12), steve.id, admin.id)
#         # End time passed, no clock_in
#         shift.start_time = datetime(2025,11,17,8)
#         shift.end_time = datetime(2025,11,17,9)
#         shift.updateStatus()
#         db.session.commit()

#         shift= Shift.query.get(shift.id)

#         summary = get_summary(schedule.id)
#         day_data = summary["days"]["2025-11-17"]
#         assert steve.username in day_data["missed"]

#     def test_get_summary_scheduled_shift(self):
#         summary = get_summary(self.schedule.id)
#         day_data = summary["days"]["2025-11-20"]
#         assert self.alice.username in day_data["scheduled"]

#     def test_get_summary_ongoing_shift(self):
#         clock_in(self.alice.id, self.shift4.id)
#         summary = get_summary(self.schedule.id)
#         day_data = summary["days"]["2025-11-20"]
#         assert self.alice.username in day_data["ongoing"]

        
