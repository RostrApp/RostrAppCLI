import os, tempfile, pytest, logging, unittest, datetime
from werkzeug.security import check_password_hash, generate_password_hash
from App.main import create_app
from App.database import db, create_db
from datetime import datetime, timedelta, date
from App.models import User, Schedule, Shift, Staff, Report
from App.services.strategies.minimum_scheduler import MinimumScheduler
from App.controllers import (
    create_user,
    get_all_users_json,
    loginCLI,
    get_user,
    update_user,
    create_schedule,
    schedule_shift, 
    schedule_week,
    view_report,
    #get_shift_report,
    #get_combined_roster,
    clock_in,
    clock_out, 
    get_summary
)

# Test get_all_users_by_role(role) and get_all_users_by_role_json(role)

LOGGER = logging.getLogger(__name__)
'''
   Unit Tests
'''


class UserUnitTests(unittest.TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()

    # User creation
    def test_new_user_admin(self):
        user = create_user("bot", "bobpass", "admin")
        assert user.username == "bot"

    def test_new_user_staff(self):
        user = create_user("pam", "pampass", "staff")
        assert user.username == "pam"

    def test_create_user_invalid_role(self):
        user = create_user("jim", "jimpass", "ceo")
        assert user is None

    def test_get_json(self):
        user = User("bob", "bobpass", "admin")
        user_json = user.get_json()
        assert user_json["username"] == "bob"
        assert user_json["role"] == "admin"

    # def test_hashed_password(self):
    #     password = "mypass"
    #     user = User(username="tester", password=password)
    #     assert user.password != password
    #     assert user.check_password(password) == True

    # def test_check_password(self):
    #     password = "mypass"
    #     user = User("bob", password)
    #     assert user.check_password(password) == True


# Admin unit tests
class AdminUnitTests(unittest.TestCase):
    
    def setUp(self):
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        app.app_context().push()
        db.drop_all()
        db.create_all()

        self.admin = create_user("admin", "adminpass", "admin")
        self.staff1 = create_user("staff1", "staffpass", "staff")
        self.staff2 = create_user("staff2", "staffpass", "staff")
        self.staff3 = create_user("staff3", "staffpass", "staff")
        self.staff_list = [self.staff1.id, self.staff2.id, self.staff3.id]
        db.session.add_all([self.admin, self.staff1, self.staff2, self.staff3])
        db.session.commit()

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=8)
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=6)


    def test_create_schedule(self):
        schedule = create_schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add(schedule)
        db.session.commit()
        assert schedule

    def test_create_schedule_invalid_role(self):
        with pytest.raises(PermissionError, match="Only admins can create schedules"):
            schedule = create_schedule(self.start_date, self.end_date, self.staff1.id)
            assert schedule is None

    def test_schedule_week_valid(self):        
        schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add(schedule)    
        db.session.commit()

        strategy = MinimumScheduler()
        schedule_week(strategy, schedule.id, self.staff_list, self.admin.id)
        shifts = schedule.get_shifts()

        assert len(schedule.shifts) == 7    # should be 1 per day
        assert shifts[0].staff_id == self.staff1.id
        assert isinstance(shifts[0], Shift)

    def test_schedule_week_invalid(self):
        invalid_schedule_id = 999
        strategy = MinimumScheduler()

        with pytest.raises(ValueError, match="Invalid schedule ID"):
            shift = schedule_week(strategy, invalid_schedule_id, self.staff_list, self.admin.id)
            assert shift is None
    
    def test_schedule_shift_valid(self):
        schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add(schedule)
        db.session.commit()

        shift = schedule_shift(schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)

        assert shift.staff_id == self.staff1.id
        assert shift.schedule_id == schedule.id
        assert shift.start_time == self.start_time
        assert shift.end_time == self.end_time
        assert isinstance(shift, Shift)

    def test_schedule_shift_invalid(self):
        invalid_schedule_id = 999
        with pytest.raises(ValueError, match="Invalid schedule ID"):
            shift = schedule_shift(invalid_schedule_id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
            assert shift is None

    def test_view_report(self):
        schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add(schedule)
        db.session.commit()

        shift1 = schedule_shift(schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
        shift2 = schedule_shift(schedule.id, self.start_time, self.end_time, self.staff2.id, self.admin.id)

        report = view_report(schedule.id, self.admin.id)
        assert isinstance(report, Report)
        self.assertEqual(report.summary["schedule_id"], schedule.id)
        self.assertIn("days", report.summary)
        assert isinstance(report.summary["days"], dict)

    def test_view_report_invalid(self):
        schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add(schedule)
        db.session.commit()

        with pytest.raises(PermissionError, match="Only admins can view shift reports"):
            report = view_report(schedule.id, self.staff1.id)
            assert report is None
    
    # Staff unit tests
class StaffUnitTests(unittest.TestCase):
    
    def setUp(self):
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        app.app_context().push()
        db.drop_all()
        db.create_all()


#     def test_view_schedule_valid(self):
#         admin = create_user("admin3", "adminpass", "admin")
#         staff = create_user("staff3", "pass123", "staff")

#         schedule = Schedule(name="Test Schedule", created_by=admin.id)
#         db.session.add(schedule)
#         db.session.commit()

#         start = datetime.now()
#         end = start + timedelta(hours=8)
#         schedule_shift(admin.id, staff.id, schedule.id, start, end)

#         from App.controllers.staff import viewSchedule
#         result = viewSchedule(staff.id, schedule.id)

#         self.assertEqual(len(result), 1)
#         self.assertEqual(result[0]["schedule_id"], schedule.id)

#     def test_view_schedule_invalid_role(self):
#         manager = create_user("notstaff123", "pass", "admin")
#         with self.assertRaises(PermissionError):
#             from App.controllers.staff import viewSchedule
#             viewSchedule(manager.id, 1)

#     def test_view_shifts_valid(self):
#         admin = create_user("admin_view", "adminpass", "admin")
#         staff = create_user("staff_view", "staffpass", "staff")

#         # Create 1 schedule to attach shifts to
#         schedule = Schedule(name="ViewShift Schedule", created_by=admin.id)
#         db.session.add(schedule)
#         db.session.commit()

#         # Create one shift for the staff
#         start = datetime.now()
#         end = start + timedelta(hours=8)
#         shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

#         # Import the controller AFTER creating data
#         from App.controllers.staff import viewShifts

#         result = viewShifts(staff.id)

#         self.assertEqual(len(result), 1)
#         self.assertEqual(result[0]["staff_id"], staff.id)
#         self.assertEqual(result[0]["schedule_id"], schedule.id)

#     def test_view_shifts_invalid_user(self):
#         admin = create_user("admin_view_bad", "adminpass", "admin")
#         with self.assertRaises(PermissionError):
#             from App.controllers.staff import viewShifts
#             viewShifts(admin.id, 1)  

    def test_clock_in_valid(self):
        admin = create_user("admin_clock", "adminpass", "admin")
        staff = create_user("staff_clock", "staffpass", "staff")
        db.session.add_all([admin, staff]); db.session.commit()

        schedule = Schedule(
            start_date=datetime(2025, 10, 25, 8),
            end_date=datetime(2025, 10, 25, 16),
            admin_id=admin.id
        )
        db.session.add(schedule); db.session.commit()

#         start = datetime.now()
#         end = start + timedelta(hours=8)
#         shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clocked_in_shift = clock_in(staff.id, shift.id)
        assert clocked_in_shift.clock_in is not None

    def test_clock_in_invalid_user(self):
        admin = create_user("admin_clockin", "adminpass", "admin")
        staff = create_user("staff_invalid", "staffpass", "staff")
        start = datetime.now()
        end = start + timedelta(hours=8)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        schedule = Schedule(
            start_date=datetime(2025, 10, 26, 8),
            end_date=datetime(2025, 10, 26, 16),
            admin_id=admin.id
        )
        db.session.add(schedule); db.session.commit()

        shift = schedule_shift(schedule.id,
                               datetime(2025, 10, 26, 8),
                               datetime(2025, 10, 26, 16),
                               staff.id,
                               admin.id)
        
        with pytest.raises(PermissionError) as e:
            clock_in(admin.id, shift.id)
        assert str(e.value) == "Only staff can clock in"

    def test_clock_in_invalid_shift(self):
        staff = create_user("clockstaff_invalid", "clockpass", "staff")
        db.session.add(staff); db.session.commit()

        with pytest.raises(ValueError) as e:
            clock_in(staff.id, 999)
        assert str(e.value) == "Invalid shift for staff"

    def test_clock_out_valid(self):
        admin = create_user("admin_clockout", "adminpass", "admin")
        staff = create_user("staff_clockout", "staffpass", "staff")
        db.session.add_all([admin, staff]); db.session.commit()

        schedule = Schedule(
            start_date=datetime(2025, 10, 27, 8),
            end_date=datetime(2025, 10, 27, 16),
            admin_id=admin.id
        )
        db.session.add(schedule); db.session.commit()

#         start = datetime.now()
#         end = start + timedelta(hours=8)
#         shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clock_in(staff.id, shift.id)
        clocked_out_shift = clock_out(staff.id, shift.id)
        assert clocked_out_shift.clock_out is not None
        assert isinstance(clocked_out_shift.clock_out, datetime)

#     def test_clock_out_invalid_user(self):
#         admin = create_user("admin_invalid_out", "adminpass", "admin")
#         schedule = Schedule(name="Invalid ClockOut Schedule",
#                             created_by=admin.id)
#         db.session.add(schedule)
#         db.session.commit()

#         staff = create_user("staff_invalid_out", "staffpass", "staff")
#         start = datetime.now()
#         end = start + timedelta(hours=8)
#         shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

#         with pytest.raises(PermissionError) as e:
#             clock_out(admin.id, shift.id)
#         assert str(e.value) == "Only staff can clock out"

#     def test_clock_out_invalid_shift(self):
#         staff = create_user("staff_invalid_shift_out", "staffpass", "staff")
#         with pytest.raises(ValueError) as e:
#             clock_out(staff.id, 999)
#         assert str(e.value) == "Invalid shift for staff"


class ReportUnitTests(unittest.TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()
        self.admin = create_user("admin_summary", "pass123", "admin")
        self.alice = create_user("Alice", "alicepass", "staff")
        self.bob = create_user("Bob", "bobpass", "staff")
        self.steve = create_user("Steve", "stevepass", "staff")
        db.session.add_all([self.admin, self.alice, self.bob, self.steve])
        db.session.commit()

        self.schedule = Schedule(
            start_date=datetime(2025, 11, 17, 8),
            end_date=datetime(2025, 11, 21, 16),
            admin_id=self.admin.id
        )
        db.session.add(self.schedule)
        db.session.commit()

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

    def test_get_summary_completed_shift(self):
        admin = User(username="admin_sum", password="pass", role="admin")
        alice = User(username="alice", password="pass", role="staff")
        db.session.add_all([admin, alice]); db.session.commit()

        schedule = Schedule(
            start_date=datetime(2025,11,17),
            end_date=datetime(2025,11,18),
            admin_id=admin.id
        )
        db.session.add(schedule); db.session.commit()

        shift = schedule_shift(schedule.id, datetime(2025,11,17,8), datetime(2025,11,17,12), alice.id, admin.id)
        shift.clock_in = datetime(2025,11,17,8)
        shift.clock_out = datetime(2025,11,17,12)
        shift.updateStatus()
        db.session.commit()

        summary = get_summary(schedule.id)
        day_data = summary["days"]["2025-11-17"]
        staff_user = User.query.get(shift.staff_id)
        assert staff_user.username in day_data["completed"]

    def test_get_summary_late_shift(self):
        admin = User(username="admin_sum2", password="pass", role="admin")
        bob = User(username="bob", password="pass", role="staff")
        db.session.add_all([admin, bob]); db.session.commit()

        schedule = Schedule(
            start_date=datetime(2025,11,17),
            end_date=datetime(2025,11,18),
            admin_id=admin.id
        )
        db.session.add(schedule); db.session.commit()

    
    
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now() + timedelta(hours=3)
        shift = schedule_shift(schedule.id, start, end, bob.id, admin.id)
        shift.updateStatus()
        db.session.commit()

        summary = get_summary(schedule.id)
        day_key = start.strftime("%Y-%m-%d")
        day_data = summary["days"][day_key]
        staff_user = User.query.get(shift.staff_id)
        assert staff_user.username in day_data["late"]

    def test_get_summary_missed_shift(self):
        admin = User(username="admin_sum3", password="pass", role="admin")
        steve = User(username="steve", password="pass", role="staff")
        db.session.add_all([admin, steve]); db.session.commit()

        schedule = Schedule(
            start_date=datetime(2025,11,17),
            end_date=datetime(2025,11,18),
            admin_id=admin.id
        )
        db.session.add(schedule); db.session.commit()

        shift = schedule_shift(schedule.id, datetime(2025,11,17,8), datetime(2025,11,17,12), steve.id, admin.id)
        # End time passed, no clock_in
        shift.start_time = datetime(2025,11,17,8)
        shift.end_time = datetime(2025,11,17,9)
        shift.updateStatus()
        db.session.commit()

        shift= Shift.query.get(shift.id)

        summary = get_summary(schedule.id)
        day_data = summary["days"]["2025-11-17"]
        assert steve.username in day_data["missed"]

    def test_get_summary_scheduled_shift(self):
        summary = get_summary(self.schedule.id)
        day_data = summary["days"]["2025-11-20"]
        assert self.alice.username in day_data["scheduled"]

    def test_get_summary_ongoing_shift(self):
        self.alice.clock_in(self.alice.id, self.shift4.id)
        summary = get_summary(self.schedule.id)
        day_data = summary["days"]["2025-11-20"]
        assert self.alice.username in day_data["ongoing"]

        
'''
    Integration Tests
'''


# @pytest.fixture(autouse=True)
# def clean_db():
#     db.drop_all()
#     create_db()
#     db.session.remove()
#     yield


# # This fixture creates an empty database for the test and deletes it after the test
# # scope="class" would execute the fixture once and resued for all methods in the class
# @pytest.fixture(autouse=True, scope="module")
# def empty_db():
#     app = create_app({
#         'TESTING': True,
#         'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'
#     })
#     create_db()
#     db.session.remove()
#     yield app.test_client()
#     db.drop_all()


# def test_authenticate():
#     user = User("bob", "bobpass", "user")
#     assert loginCLI("bob", "bobpass") != None

import unittest
import pytest
from datetime import datetime, timedelta
from App.database import db
from App.models import User, Schedule, Shift
from App.controllers import (
    create_user, update_user, get_user, get_all_users_json,
    schedule_shift, viewSchedule, clock_in, clock_out,
    generate_report, loginCLI
)

# Reset DB before each test to avoid conflicts
@pytest.fixture(autouse=True)
def run_around_tests():
    db.drop_all()
    db.create_all()
    yield
    db.session.remove()
    db.drop_all()


class UsersIntegrationTests(unittest.TestCase): # works

#     def test_get_user(self):
#         user = create_user("bob", "bobpass", "admin")
#         assert()

    def test_get_all_users_json(self):
        user = create_user("bob", "bobpass", "admin")
        user = create_user("pam", "pampass", "staff")
        users_json = get_all_users_json()
        self.assertListEqual([
            {"id": 1, "username": "bot", "role": "admin"},
            {"id": 2, "username": "pam", "role": "staff"}
        ], users_json)

    def test_update_user(self):
        create_user("bot", "bobpass", "admin")
        update_user(1, "ronnie")
        user = get_user(1)
        assert user.username == "ronnie"

#     def test_create_and_get_user(self):
#         user = create_user("alex", "alexpass", "staff")
#         retrieved = get_user(user.id)
#         self.assertEqual(retrieved.username, "alex")
#         self.assertEqual(retrieved.role, "staff")

    def test_get_all_users_json_integration(self):
        create_user("bot", "bobpass", "admin")
        create_user("pam", "pampass", "staff")
        users_json = get_all_users_json()
        expected = [
            {"id": 1, "username": "bot", "role": "admin"},
            {"id": 2, "username": "pam", "role": "staff"},
        ]
        self.assertEqual(users_json, expected)

#     def test_admin_schedule_shift_for_staff(self):
#         admin = create_user("admin1", "adminpass", "admin")
#         staff = create_user("staff1", "staffpass", "staff")

        schedule = Schedule(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            admin_id=admin.id
        )
        db.session.add(schedule)
        db.session.commit()

#         start = datetime.now()
#         end = start + timedelta(hours=8)

        shift = schedule_shift(schedule.id, start, end, staff.id, admin.id)
        retrieved = get_user(staff.id)

#         self.assertIn(shift.id, [s.id for s in retrieved.shifts])
#         self.assertEqual(shift.staff_id, staff.id)
#         self.assertEqual(shift.schedule_id, schedule.id)

#     # def test_staff_view_combined_roster(self):
#     #     admin = create_user("admin", "adminpass", "admin")
#     #     staff = create_user("jane", "janepass", "staff")
#     #     other_staff = create_user("mark", "markpass", "staff")

#     #     schedule = Schedule(name="Shared Roster", created_by=admin.id)
#     #     db.session.add(schedule)
#     #     db.session.commit()

#     #     start = datetime.now()
#     #     end = start + timedelta(hours=8)

#     #     schedule_shift(admin.id, staff.id, schedule.id, start, end)
#     #     schedule_shift(admin.id, other_staff.id, schedule.id, start, end)

#     #     roster = get_combined_roster(staff.id)
#     #     self.assertTrue(any(s["staff_id"] == staff.id for s in roster))
#     #     self.assertTrue(any(s["staff_id"] == other_staff.id for s in roster))

#     def test_staff_clock_in_and_out(self):
#         admin = create_user("admin", "adminpass", "admin")
#         staff = create_user("lee", "leepass", "staff")

        schedule = Schedule(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            admin_id=admin.id
        )
        db.session.add(schedule)
        db.session.commit()

#         start = datetime.now()
#         end = start + timedelta(hours=8)

        shift = schedule_shift(schedule.id, start, end, staff.id, admin.id)

#         clock_in(staff.id, shift.id)
#         clock_out(staff.id, shift.id)

        updated_shift = Shift.query.get(shift.id)
        self.assertIsNotNone(updated_shift.clock_in)
        self.assertIsNotNone(updated_shift.clock_out)
        self.assertLess(updated_shift.clock_in, updated_shift.clock_out)

#     # def test_permission_restrictions(self):
#     #     admin = create_user("admin", "adminpass", "admin")
#     #     staff = create_user("worker", "workpass", "staff")

#     #     # Create schedule
#     #     schedule = Schedule(name="Restricted Schedule", created_by=admin.id)
#     #     db.session.add(schedule)
#     #     db.session.commit()

#     #     start = datetime.now()
#     #     end = start + timedelta(hours=8)

#     #     with self.assertRaises(PermissionError):
#     #         schedule_shift(staff.id, staff.id, schedule.id, start, end)

#     #     with self.assertRaises(PermissionError):
#     #         get_combined_roster(admin.id)

#     #     with self.assertRaises(PermissionError):
#     #         get_shift_report(staff.id)

# import unittest
# from datetime import datetime
# from App.database import db
# from App.models.user import User
# from App.models.shift import Shift
# from App.models.schedule import Schedule
# from App.services.strategies.even_scheduler import EvenScheduler
# from App.services.strategies.minimum_scheduler import MinimumScheduler
# from App.services.strategies.day_night_scheduler import DayNightScheduler

class ScheduleUnitTests(unittest.TestCase): #works

    def setUp(self):
        # Clear DB before each test
        db.drop_all()
        db.create_all()
        # Create staff users
        self.staff1 = User(username="jane", password="pass", role="staff")
        self.staff2 = User(username="alice", password="pass", role="staff")
        db.session.add_all([self.staff1, self.staff2])
        db.session.commit()

    def test_even_scheduler_assigns_equally(self):
        schedule = Schedule(
            start_date=datetime(2025, 11, 21),
            end_date=datetime(2025, 11, 22),
            admin_id=1
        )

        strategy = EvenScheduler()
        strategy.fill_schedule([self.staff1, self.staff2], schedule)

        db.session.add(schedule)
        db.session.commit()

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        staff_ids = [s.staff_id for s in shifts]
        # Expect roughly equal distribution
        self.assertTrue(abs(staff_ids.count(self.staff1.id) - staff_ids.count(self.staff2.id)) <= 1)

    def test_minimum_scheduler_assigns_first_staff(self):
        schedule = Schedule(
            start_date=datetime(2025, 11, 21),
            end_date=datetime(2025, 11, 22),
            admin_id=1
        )

        strategy = MinimumScheduler()
        strategy.fill_schedule([self.staff1, self.staff2], schedule)

        db.session.add(schedule)
        db.session.commit()

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        # Expect all shifts assigned to staff1
        for s in shifts:
            self.assertEqual(s.staff_id, self.staff1.id)

    def test_daynight_scheduler_assigns_correctly(self):
        schedule = Schedule(
            start_date=datetime(2025, 11, 21),
            end_date=datetime(2025, 11, 22),
            admin_id=1
        )

        strategy = DayNightScheduler()
        strategy.fill_schedule([self.staff1, self.staff2], schedule)

        db.session.add(schedule)
        db.session.commit()

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        for s in shifts:
            if s.start_time.hour == 8:   # Day shift
                self.assertEqual(s.staff_id, self.staff1.id)
            elif s.start_time.hour == 20:  # Night shift
                self.assertEqual(s.staff_id, self.staff2.id)

class ScheduleIntegrationTests(unittest.TestCase): #works

    def setUp(self):
        # Clear DB before each test
        db.drop_all()
        db.create_all()

        # Create admin and staff users
        self.admin = User(username="admin_sched", password="pass", role="admin")
        self.staff1 = User(username="staff1_sched", password="pass", role="staff")
        self.staff2 = User(username="staff2_sched", password="pass", role="staff")
        db.session.add_all([self.admin, self.staff1, self.staff2])
        db.session.commit()

    def test_even_scheduler_integration(self):
        schedule = Schedule(
            start_date=datetime(2025, 12, 5),
            end_date=datetime(2025, 12, 7),
            admin_id=self.admin.id
        )

        strategy = EvenScheduler()
        strategy.fill_schedule([self.staff1, self.staff2], schedule)

        db.session.add(schedule)
        db.session.commit()

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        staff_ids = [s.staff_id for s in shifts]

        # Expect roughly equal distribution
        self.assertTrue(abs(staff_ids.count(self.staff1.id) - staff_ids.count(self.staff2.id)) <= 1)

    def test_minimum_scheduler_integration(self):
        schedule = Schedule(
            start_date=datetime(2025, 12, 5),
            end_date=datetime(2025, 12, 6),
            admin_id=self.admin.id
        )

        strategy = MinimumScheduler()
        strategy.fill_schedule([self.staff1, self.staff2], schedule)

        db.session.add(schedule)
        db.session.commit()

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        # Expect all shifts assigned to staff1
        for s in shifts:
            self.assertEqual(s.staff_id, self.staff1.id)

    def test_daynight_scheduler_integration(self):
        schedule = Schedule(
            start_date=datetime(2025, 12, 5),
            end_date=datetime(2025, 12, 6),
            admin_id=self.admin.id
        )

        strategy = DayNightScheduler()
        strategy.fill_schedule([self.staff1, self.staff2], schedule)

#         db.session.add(schedule)
#         db.session.commit()

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        for s in shifts:
            if s.start_time.hour == 8:   # Day shift
                self.assertEqual(s.staff_id, self.staff1.id)
            elif s.start_time.hour == 18:  # Night shift
                self.assertEqual(s.staff_id, self.staff2.id)


# import pytest
# from datetime import datetime
# from App.main import create_app
# from App.database import db
# from App.models import User, Schedule, Shift
# from App.services.strategies.even_scheduler import EvenScheduler
# from App.services.strategies.minimum_scheduler import MinimumScheduler
# from App.services.strategies.day_night_scheduler import DayNightScheduler

# @pytest.fixture
# def test_app():
#     app = create_app("testing")
#     with app.app_context():
#         db.drop_all()
#         db.create_all()
#         yield app
#         db.session.remove()
#         db.drop_all()


import unittest
from datetime import datetime
from App.models import User, Schedule, Shift
from App.services.strategies.even_scheduler import EvenScheduler 
from App.services.strategies.minimum_scheduler import MinimumScheduler
from App.services.strategies.day_night_scheduler import DayNightScheduler
from App.controllers.admin import schedule_week
from App.database import db

# class TestSchedulerIntegration(unittest.TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()

        # Create admin + staff
        self.admin = User(username="admin", password="pass", role="admin")
        self.staff1 = User(username="s1", password="pass", role="staff")
        self.staff2 = User(username="s2", password="pass", role="staff")
        db.session.add_all([self.admin, self.staff1, self.staff2])
        db.session.commit()

    def test_admin_schedule_week_even(self):
        schedule = Schedule(
            start_date=datetime(2025, 12, 2),
            end_date=datetime(2025, 12, 4),
            admin_id=self.admin.id
        )
        db.session.add(schedule)
        db.session.commit()

        schedule_week(EvenScheduler(), schedule.id, [self.staff1.id, self.staff2.id], self.admin.id)

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        staff_ids = [s.staff_id for s in shifts]
        # Expect roughly even distribution
        self.assertTrue(abs(staff_ids.count(self.staff1.id) - staff_ids.count(self.staff2.id)) <= 1)

    def test_admin_schedule_week_minimum(self):
        schedule = Schedule(
            start_date=datetime(2025, 12, 2),
            end_date=datetime(2025, 12, 4),
            admin_id=self.admin.id
        )
        db.session.add(schedule)
        db.session.commit()

        schedule_week(MinimumScheduler(), schedule.id, [self.staff1.id, self.staff2.id], self.admin.id)

#         shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
#         # Expect all shifts assigned to staff1
#         for s in shifts:
#             self.assertEqual(s.staff_id, self.staff1.id)

    def test_admin_schedule_week_daynight(self):
        schedule = Schedule(
            start_date=datetime(2025, 12, 2),
            end_date=datetime(2025, 12, 3),
            admin_id=self.admin.id
        )
        db.session.add(schedule)
        db.session.commit()

        schedule_week(DayNightScheduler(), schedule.id, [self.staff1.id, self.staff2.id], self.admin.id)

#         shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
#         for s in shifts:
#             if s.start_time.hour == 8:
#                 self.assertEqual(s.staff_id, self.staff1.id)
#             elif s.start_time.hour == 18:
#                 self.assertEqual(s.staff_id, self.staff2.id)
