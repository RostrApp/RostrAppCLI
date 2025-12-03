import os, tempfile, pytest, logging, unittest, datetime
from werkzeug.security import check_password_hash, generate_password_hash
from App.main import create_app
from App.database import db, create_db
from datetime import datetime, timedelta, date
from App.models import User, Schedule, Shift, Staff, Report
from App.services.strategies.minimum_scheduler import MinimumScheduler
from App.controllers import (
    create_user,
    create_schedule,
    schedule_shift, 
    schedule_week,
    view_report,
    view_schedule,
    view_shifts,
    clock_in,
    clock_out, 
    get_summary
)

LOGGER = logging.getLogger(__name__)
'''
   Unit Tests
'''

class UserUnitTests(unittest.TestCase):

    def setUp(self):
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        app.app_context().push()
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

    def test_hashed_password(self):
        password = "mypass"
        user = User(username="tester", password=password)
        assert user.password != password
        assert user.check_password(password) == True

    def test_check_password(self):
        password = "mypass"
        user = User("bob", password)
        assert user.check_password(password) == True


# Admin unit tests
class AdminUnitTests(unittest.TestCase):
    
    def setUp(self):                # can reuse this code since none of it is being tested for Admin tests
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
        db.session.add_all([shift1, shift2])
        db.session.commit()

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
    
    def setUp(self):            # can reuse this code since none of it is being tested for Staff tests
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        app.app_context().push()
        db.drop_all()
        db.create_all()

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=8)
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=6)

        self.admin = create_user("admin", "adminpass", "admin")
        self.staff = create_user("staff", "pass123", "staff")
        self.schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add_all([self.admin, self.staff, self.schedule])
        db.session.commit()

        self.shift = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff.id, self.admin.id)
        db.session.add(self.shift)
        db.session.commit()


    def test_view_schedule_valid(self):
        result = view_schedule(self.staff.id, self.schedule.id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["schedule_id"], self.schedule.id)

    def test_view_schedule_invalid_role(self):
        with self.assertRaises(PermissionError):
            view_schedule(self.admin.id, 1)

    def test_view_shifts_valid(self):
        result = view_shifts(self.staff.id, self.schedule.id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["staff_id"], self.staff.id)
        self.assertEqual(result[0]["schedule_id"], self.schedule.id)

    def test_view_shifts_invalid_user(self):
        admin = create_user("admin_view_bad", "adminpass", "admin")
        with self.assertRaises(PermissionError):
            view_shifts(admin.id, 1)  

    def test_clock_in_valid(self):
        clocked_in_shift = clock_in(self.staff.id, self.shift.id)
        assert clocked_in_shift.clock_in is not None

    def test_clock_in_invalid_user(self):      
        with self.assertRaises(PermissionError):
            clock_in(self.admin.id, self.shift.id)

    def test_clock_in_invalid_shift(self):
        with self.assertRaises(ValueError):
            clock_in(self.staff.id, 999)

    def test_clock_in_duplicate(self):      
        with self.assertRaises(ValueError):
            clock_in(self.staff.id, self.shift.id)
            clock_in(self.staff.id, self.shift.id)

    def test_clock_out_valid(self):
        clock_in(self.staff.id, self.shift.id)
        clocked_out_shift = clock_out(self.staff.id, self.shift.id)
        assert clocked_out_shift.clock_out is not None
        assert isinstance(clocked_out_shift.clock_out, datetime)

    def test_clock_out_invalid_user(self):
        with self.assertRaises(PermissionError):
            clock_out(self.admin.id, self.shift.id)

    def test_clock_out_invalid_shift(self):
        with pytest.raises(ValueError):
            clock_out(self.staff.id, 999)

    def test_clock_out_duplicate(self):
        clock_in(self.staff.id, self.shift.id)      
        with self.assertRaises(ValueError):
            clock_out(self.staff.id, self.shift.id)
            clock_out(self.staff.id, self.shift.id)


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

        self.shift1 = Shift(staff_id=self.alice.id,
                    schedule_id=self.schedule.id,
                    start_time=datetime(2025, 11, 17, 8),
                    end_time=datetime(2025, 11, 17, 16),
                    clock_in=datetime(2025, 11, 17, 8, 5),
                    clock_out=datetime(2025, 11, 17, 16))

        self.shift2 = Shift(staff_id=self.bob.id,
                    schedule_id=self.schedule.id,
                    start_time=datetime(2025, 11, 17, 8),
                    end_time=datetime(2025, 11, 17, 16),
                    clock_in=datetime(2025, 11, 17, 8, 0),
                    clock_out=datetime(2025, 11, 17, 16))

        self.shift3 = Shift(staff_id=self.steve.id,
                    schedule_id=self.schedule.id,
                    start_time=datetime(2025, 11, 17, 8),
                    end_time=datetime(2025, 11, 17, 16))

        self.shift4 = Shift(staff_id=self.alice.id,
                    schedule_id=self.schedule.id,
                    start_time=datetime(2025, 11, 20, 8),
                    end_time=datetime(2025, 11, 20, 16))

        db.session.add_all([self.shift1, self.shift2, self.shift3, self.shift4])
        db.session.commit()

    def test_get_summary_invalid_schedule(self):
        with pytest.raises(ValueError):
            get_summary(99999)

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
        clock_in(self.alice.id, self.shift4.id)
        summary = get_summary(self.schedule.id)
        day_data = summary["days"]["2025-11-20"]
        assert self.alice.username in day_data["ongoing"]

            
import os, tempfile, pytest, logging, unittest, datetime
from datetime import datetime, timedelta, date
from App.main import create_app
from App.database import db, create_db
from App.models import User, Schedule, Shift, Staff, Report
from App.services.strategies.even_scheduler import EvenScheduler
from App.services.strategies.minimum_scheduler import MinimumScheduler
from App.services.strategies.day_night_scheduler import DayNightScheduler
from App.controllers import (
    create_user,
    update_user, 
    get_user_by_username,
    get_user, 
    get_all_users,
    get_all_users_json,
    get_all_users_by_role,
    get_all_users_by_role_json,
    schedule_week,
    schedule_shift,
    clock_in, 
    clock_out,
    get_summary, 
    loginCLI
)

'''
    Integration Tests
'''


@pytest.fixture(autouse=True)
def clean_db():
    db.drop_all()
    create_db()
    db.session.remove()
    yield


# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="module")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    app.app_context().push()
    create_db()
    db.session.remove()
    yield app.test_client()
    db.drop_all()


def test_authenticate():
    user = User("bob", "bobpass", "user")
    assert loginCLI("bob", "bobpass") != None

# Reset DB before each test to avoid conflicts
@pytest.fixture(autouse=True)
def run_around_tests():
    db.drop_all()
    db.create_all()
    yield
    db.session.remove()
    db.drop_all()


class UsersIntegrationTests(unittest.TestCase):

    def setUp(self):
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        app.app_context().push()
        db.drop_all()
        db.create_all()

    def test_create_user(self):
        user = create_user("bob", "bobpass", "admin")
        assert user.id == 1

    def test_create_user_invalid(self):
        user = create_user("bob", "bobpass", "ceo")
        assert user is None

    def test_get_user(self):
        user = create_user("bob", "bobpass", "admin")
        result = get_user(user.id)
        self.assertEqual(result.id, user.id)

    def test_get_user_invalid_id(self):
        user = create_user("bob", "bobpass", "admin")
        result = get_user(999)
        assert result is None

    def test_get_user_by_username(self):
        user = create_user("bob", "bobpass", "admin")
        result = get_user_by_username("bob")
        self.assertEqual(result.username, "bob")

    def test_get_user_by_username_invalid(self):
        user = create_user("bob", "bobpass", "admin")
        result = get_user_by_username("potato")
        assert result is None

    def test_get_all_users(self):
        user1 = create_user("bob", "bobpass", "admin")
        user2 = create_user("pam", "pampass", "staff")
        users = get_all_users()
        assert len(users) == 2

    def test_get_all_users_json(self):
        user1 = create_user("bob", "bobpass", "admin")
        user2 = create_user("pam", "pampass", "staff")
        users_json = get_all_users_json()
        self.assertListEqual([
            {"id": 1, "username": "bob", "role": "admin"},
            {"id": 2, "username": "pam", "role": "staff"}
        ], users_json)

    def test_get_all_users_by_role(self):
        user1 = create_user("bob", "bobpass", "admin")
        user2 = create_user("pam", "pampass", "staff")
        users = get_all_users_by_role("admin")
        assert len(users) == 1

    def test_get_all_users_by_role_json(self):
        user1 = create_user("bob", "bobpass", "admin")
        user2 = create_user("pam", "pampass", "staff")
        users_json = get_all_users_by_role_json("admin")
        self.assertListEqual([
            {"id": 1, "username": "bob", "role": "admin"},
        ], users_json)

    def test_update_user(self):
        create_user("bot", "bobpass", "admin")
        update_user(1, "ronnie")
        user = get_user(1)
        assert user.username == "ronnie"



class AdminIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.admin = create_user("admin1", "adminpass", "admin")
        self.staff = create_user("staff1", "staffpass", "staff")
        self.staff2 = create_user("staff2", "staffpass", "staff")
        self.staff3 = create_user("staff3", "staffpass", "staff")

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=8)
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=6)

        self.schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add_all([self.admin, self.staff, self.schedule])
        db.session.commit()


    def test_admin_schedule_shift_for_week(self):
        staff_list = get_all_users_by_role("staff")
        staff_id_list = []
        for staff in staff_list:
            staff_id_list.append(staff.id)

        schedule_week(EvenScheduler(), self.schedule.id, staff_id_list, self.admin.id)
        for staff_id in staff_id_list:
            self.assertIn(staff_id, [s.staff_id for s in self.schedule.shifts])
        

    def test_admin_schedule_shift_for_staff(self):
        shift = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff.id, self.admin.id)
        retrieved = get_user(self.staff.id)

        self.assertIn(shift.id, [s.id for s in retrieved.shifts])
        self.assertEqual(shift.staff_id, self.staff.id)
        self.assertEqual(shift.schedule_id, self.schedule.id)

class StaffIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.admin = create_user("admin1", "adminpass", "admin")
        self.staff = create_user("staff1", "staffpass", "staff")

    def test_staff_view_combined_roster(self):
        admin = create_user("admin", "adminpass", "admin")
        staff = create_user("jane", "janepass", "staff")
        other_staff = create_user("mark", "markpass", "staff")

        schedule = Schedule(name="Shared Roster", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        schedule_shift(admin.id, staff.id, schedule.id, start, end)
        schedule_shift(admin.id, other_staff.id, schedule.id, start, end)

        roster = get_combined_roster(staff.id)
        self.assertTrue(any(s["staff_id"] == staff.id for s in roster))
        self.assertTrue(any(s["staff_id"] == other_staff.id for s in roster))

    def test_staff_clock_in_and_out(self):
        admin = create_user("admin", "adminpass", "admin")
        staff = create_user("lee", "leepass", "staff")

        schedule = Schedule(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            admin_id=admin.id
        )
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        shift = schedule_shift(schedule.id, start, end, staff.id, admin.id)

        clock_in(staff.id, shift.id)
        clock_out(staff.id, shift.id)

        updated_shift = Shift.query.get(shift.id)
        self.assertIsNotNone(updated_shift.clock_in)
        self.assertIsNotNone(updated_shift.clock_out)
        self.assertLess(updated_shift.clock_in, updated_shift.clock_out)

    def test_permission_restrictions(self):
        admin = create_user("admin", "adminpass", "admin")
        staff = create_user("worker", "workpass", "staff")

        # Create schedule
        schedule = Schedule(name="Restricted Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        with self.assertRaises(PermissionError):
            schedule_shift(staff.id, staff.id, schedule.id, start, end)

        with self.assertRaises(PermissionError):
            get_combined_roster(admin.id)

        with self.assertRaises(PermissionError):
            get_shift_report(staff.id)




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



class TestSchedulerIntegration(unittest.TestCase):

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

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        # Expect all shifts assigned to staff1
        for s in shifts:
            self.assertEqual(s.staff_id, self.staff1.id)

    def test_admin_schedule_week_daynight(self):
        schedule = Schedule(
            start_date=datetime(2025, 12, 2),
            end_date=datetime(2025, 12, 3),
            admin_id=self.admin.id
        )
        db.session.add(schedule)
        db.session.commit()

        schedule_week(DayNightScheduler(), schedule.id, [self.staff1.id, self.staff2.id], self.admin.id)

        shifts = Shift.query.filter_by(schedule_id=schedule.id).all()
        for s in shifts:
            if s.start_time.hour == 8:
                self.assertEqual(s.staff_id, self.staff1.id)
            elif s.start_time.hour == 18:
                self.assertEqual(s.staff_id, self.staff2.id)

class ReportIntegrationTests(unittest.TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.admin = create_user("admin", "adminpass", "admin")
        self.staff = create_user("staff", "staffpass", "staff")
        # self.staff2 = create_user("staff2", "staffpass", "staff")
        # self.staff3 = create_user("staff3", "staffpass", "staff")
        # self.staff4 = create_user("staff4", "staffpass", "staff")
        self.staff_list = [self.staff.id] #, self.staff2.id, self.staff3.id]
        db.session.add_all([self.admin, self.staff]) #, self.staff2, self.staff3])
        db.session.commit()

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=8)
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=6)

        self.schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add(self.schedule)
        db.session.commit()

        self.shift = schedule_shift(self.schedule.id, self.start_date, self.end_date, self.staff.id, self.admin.id)
        db.session.add(self.shift)
        db.session.commit()

    def test_get_summary_completed_shift(self):
        
        self.shift.clock_in = self.start_time
        self.shift.clock_out = self.end_time
        self.shift.updateStatus()
        db.session.commit()

        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        staff_user = User.query.get(self.shift.staff_id)
        assert staff_user.username in day_data["completed"]

    def test_get_summary_late_shift(self):
        self.shift.clock_in = self.start_date - timedelta(hours=1)
        self.shift.clock_out = self.end_time
        self.shift.updateStatus()
        db.session.commit()

        summary = get_summary(self.schedule.id)
        day_key = self.shift.clock_in.strftime("%Y-%m-%d")
        day_data = summary["days"][day_key]
        staff_user = User.query.get(self.shift.staff_id)
        assert staff_user.username in day_data["late"]

    def test_get_summary_missed_shift(self):
        self.shift.updateStatus()
        db.session.commit()
        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        assert self.staff.username in day_data["missed"]

    def test_get_summary_scheduled_shift(self):
        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        assert self.staff.username in day_data["scheduled"]

    def test_get_summary_ongoing_shift(self):
        clock_in(self.staff.id, self.shift.id)
        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        assert self.staff.username in day_data["ongoing"]
