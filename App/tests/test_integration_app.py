import os, tempfile, pytest, logging, unittest, datetime, time
from datetime import datetime, timedelta, date
from App.main import create_app
from App.database import db, create_db
from App.models import User, Schedule, Shift
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
    view_shifts,
    view_schedule,
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
        db.session.add_all([self.admin, self.staff, self.staff2, self.staff3, self.schedule])
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
        self.staff1 = create_user("staff1", "staffpass", "staff")
        self.staff2 = create_user("staff2", "staffpass", "staff")

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=8)
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=6)

        self.schedule = Schedule(self.start_date, self.end_date, self.admin.id)

        db.session.add_all([self.admin, self.staff1, self.staff2, self.schedule])
        db.session.commit()

    def test_staff_view_shifts(self):
        shift1 = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
        shift2 = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff2.id, self.admin.id)

        shifts = view_shifts(self.staff1.id, self.schedule.id)
        assert len(shifts) == 1
        assert shifts[0]["staff_id"] == self.staff1.id
        assert "start_time" in shifts[0]

    def test_staff_view_schedule(self):
        shift1 = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
        shift2 = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff2.id, self.admin.id)

        schedule = view_schedule(self.staff1.id, self.schedule.id)
        self.assertTrue(any(s["staff_id"] == self.staff1.id for s in schedule))
        self.assertTrue(any(s["staff_id"] == self.staff2.id for s in schedule))

    def test_staff_clock_in_ongoing_shift(self):
        shift = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
        clock_in(self.staff1.id, shift.id)
        updated_shift = Shift.query.get(shift.id)
        assert updated_shift.clock_in is not None
        assert updated_shift.status.value == "Ongoing"
        

    def test_staff_clock_in_completed_shift(self):
        shift = schedule_shift(self.schedule.id, self.start_time, self.end_time, self.staff1.id, self.admin.id)
        clock_in(self.staff1.id, shift.id)
        time.sleep(1)       # so clock_out time will be later
        clock_out(self.staff1.id, shift.id)

        updated_shift = Shift.query.get(shift.id)
        self.assertIsNotNone(updated_shift.clock_in)
        self.assertIsNotNone(updated_shift.clock_out)
        self.assertLess(updated_shift.clock_in, updated_shift.clock_out)
        self.assertEquals(updated_shift.status.value, "Completed")

    def test_permission_restrictions(self):
        with self.assertRaises(PermissionError):
            view_shifts(self.admin.id, self.schedule.id)
        with self.assertRaises(PermissionError):
            view_schedule(self.admin.id, self.schedule.id)




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
        self.admin = create_user("admin", "adminpass", "admin")
        self.staff = create_user("staff", "staffpass", "staff")
        self.staff_list = [self.staff.id]
        db.session.add_all([self.admin, self.staff])
        db.session.commit()

        self.start_time = datetime.now() - timedelta(hours=1)
        self.end_time = self.start_time + timedelta(hours=8)
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=6)

        self.schedule = Schedule(self.start_date, self.end_date, self.admin.id)
        db.session.add(self.schedule)
        db.session.commit()


    def test_get_summary_completed_shift(self):
        self.shift = schedule_shift(self.schedule.id, self.start_date, self.end_date, self.staff.id, self.admin.id)

        self.shift.clock_in = self.start_time
        self.shift.clock_out = self.end_time
        self.shift.updateStatus()
        db.session.commit()

        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        staff_user = User.query.get(self.shift.staff_id)
        assert staff_user.username in day_data["completed"]

    def test_get_summary_late_shift(self):
        self.shift = schedule_shift(self.schedule.id, self.start_date, self.end_date, self.staff.id, self.admin.id)
        self.shift.updateStatus()
        db.session.commit()

        summary = get_summary(self.schedule.id)
        day_key = self.start_time.strftime("%Y-%m-%d")
        day_data = summary["days"][day_key]
        staff_user = User.query.get(self.shift.staff_id)
        assert staff_user.username in day_data["late"]

    def test_get_summary_missed_shift(self):
        start = self.start_date - timedelta(hours=1)
        end = datetime.now() - timedelta(hours=1)       # clock_out time is in the past
        self.shift = schedule_shift(self.schedule.id, start, end, self.staff.id, self.admin.id)

        self.shift.updateStatus()
        db.session.commit()
        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        assert self.staff.username in day_data["missed"]

    def test_get_summary_scheduled_shift(self):
        self.shift = schedule_shift(self.schedule.id, self.start_date, self.end_date, self.staff.id, self.admin.id)

        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        assert self.staff.username in day_data["scheduled"]

    def test_get_summary_ongoing_shift(self):
        self.shift = schedule_shift(self.schedule.id, self.start_date, self.end_date, self.staff.id, self.admin.id)

        clock_in(self.staff.id, self.shift.id)
        summary = get_summary(self.schedule.id)
        day_data = summary["days"][self.start_time.strftime("%Y-%m-%d")]
        assert self.staff.username in day_data["ongoing"]