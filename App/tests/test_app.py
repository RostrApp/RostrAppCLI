import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash
from App.main import create_app
from App.database import db, create_db
from datetime import datetime, timedelta
from App.models import User, Schedule, Shift, Staff, Report
from App.controllers import (create_user, get_all_users_json, loginCLI,
                             get_user, update_user, schedule_shift,
                             get_shift_report, get_combined_roster, clock_in,
                             clock_out, get_shift, get_summary)

# Test get_all_users_by_role(role) and get_all_users_by_role_json(role)

LOGGER = logging.getLogger(__name__)
'''
   Unit Tests
'''


class UserUnitTests(unittest.TestCase):

    # User unit tests
    def test_new_user_admin(self):
        user = create_user("bot", "bobpass", "admin")
        assert user.username == "bot"

    def test_new_user_staff(self):
        user = create_user("pam", "pampass", "staff")
        assert user.username == "pam"

    def test_create_user_invalid_role(self):
        user = create_user("jim", "jimpass", "ceo")
        assert user == None

    def test_get_json(self):
        user = User("bob", "bobpass", "admin")
        user_json = user.get_json()
        self.assertDictEqual(user_json, {
            "id": None,
            "username": "bob",
            "role": "admin"
        })

    def test_hashed_password(self):
        password = "mypass"
        user = User(username="tester", password=password)
        assert user.password != password
        assert user.check_password(password) is True

    def test_check_password(self):
        password = "mypass"
        user = User("bob", password)
        assert user.check_password(password)
# Admin unit tests

    def test_schedule_shift_valid(self):
        admin = create_user("admin1", "adminpass", "admin")
        staff = create_user("staff1", "staffpass", "staff")
        schedule = Schedule(name="Morning Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 10, 22, 8, 0, 0)
        end = datetime(2025, 10, 22, 16, 0, 0)

        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        assert shift.staff_id == staff.id
        assert shift.schedule_id == schedule.id
        assert shift.start_time == start
        assert shift.end_time == end
        assert isinstance(shift, Shift)

    def test_schedule_shift_invalid(self):
        admin = User("admin2", "adminpass", "admin")
        staff = User("staff2", "staffpass", "staff")
        invalid_schedule_id = 999

        start = datetime(2025, 10, 22, 8, 0, 0)
        end = datetime(2025, 10, 22, 16, 0, 0)
        try:
            shift = schedule_shift(admin.id, staff.id, invalid_schedule_id,
                                   start, end)
            assert shift is None
        except Exception:
            assert True

    def test_get_shift_report(self):
        admin = create_user("superadmin", "superpass", "admin")
        staff = create_user("worker1", "workerpass", "staff")
        db.session.add_all([admin, staff])
        db.session.commit()

        schedule = Schedule(name="Weekend Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        shift1 = schedule_shift(admin.id, staff.id, schedule.id,
                                datetime(2025, 10, 26, 8, 0, 0),
                                datetime(2025, 10, 26, 16, 0, 0))
        shift2 = schedule_shift(admin.id, staff.id, schedule.id,
                                datetime(2025, 10, 27, 8, 0, 0),
                                datetime(2025, 10, 27, 16, 0, 0))

        report = get_shift_report(admin.id)
        assert len(report) >= 2
        assert report[0]["staff_id"] == staff.id
        assert report[0]["schedule_id"] == schedule.id

    def test_get_shift_report_invalid(self):
        non_admin = User("randomstaff", "randompass", "staff")

        try:
            get_shift_report(non_admin.id)
            assert False, "Expected PermissionError for non-admin user"
        except PermissionError as e:
            assert str(e) == "Only admins can view shift reports"
# Staff unit tests

    def test_view_schedule_valid(self):
        admin = create_user("admin3", "adminpass", "admin")
        staff = create_user("staff3", "pass123", "staff")

        schedule = Schedule(name="Test Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)
        schedule_shift(admin.id, staff.id, schedule.id, start, end)
        
        from App.controllers.staff import viewSchedule
        result = viewSchedule(staff.id, schedule.id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["schedule_id"], schedule.id)
        
    def test_view_schedule_invalid_role(self):
        manager = create_user("notstaff123", "pass", "admin")
        with self.assertRaises(PermissionError):
            from App.controllers.staff import viewSchedule
            viewSchedule(manager.id, 1)
            
    def test_view_shifts_valid(self):
        admin = create_user("admin_view", "adminpass", "admin")
        staff = create_user("staff_view", "staffpass", "staff")

        # Create 1 schedule to attach shifts to
        schedule = Schedule(name="ViewShift Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        # Create one shift for the staff
        start = datetime.now()
        end = start + timedelta(hours=8)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        # Import the controller AFTER creating data
        from App.controllers.staff import viewShifts
        
        result = viewShifts(staff.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["staff_id"], staff.id)
        self.assertEqual(result[0]["schedule_id"], schedule.id)
        
    def test_view_shifts_invalid_user(self):
        admin = create_user("admin_view_bad", "adminpass", "admin")
        with self.assertRaises(PermissionError):
            from App.controllers.staff import viewShifts
            viewShifts(admin.id, 1)    


    def test_clock_in_valid(self):
        admin = create_user("admin_clock", "adminpass", "admin")
        staff = create_user("staff_clock", "staffpass", "staff")

        schedule = Schedule(name="Clock Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)
        
        clocked_in_shift = clock_in(staff.id, shift.id)
        assert clocked_in_shift.clock_in is not None
        assert isinstance(clocked_in_shift.clock_in, datetime)

    def test_clock_in_invalid_user(self):
        admin = create_user("admin_clockin", "adminpass", "admin")
        schedule = Schedule(name="Invalid Clock In", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        staff = create_user("staff_invalid", "staffpass", "staff")
        start = datetime.now()
        end = start + timedelta(hours=8)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        with pytest.raises(PermissionError) as e:
            clock_in(admin.id, shift.id)
        assert str(e.value) == "Only staff can clock in"

    def test_clock_in_invalid_shift(self):
        staff = create_user("clockstaff_invalid", "clockpass", "staff")
        with pytest.raises(ValueError) as e:
            clock_in(staff.id, 999)
        assert str(e.value) == "Invalid shift for staff"

    def test_clock_out_valid(self):
        admin = create_user("admin_clockout", "adminpass", "admin")
        staff = create_user("staff_clockout", "staffpass", "staff")

        schedule = Schedule(name="ClockOut Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clocked_out_shift = clock_out(staff.id, shift.id)
        assert clocked_out_shift.clock_out is not None
        assert isinstance(clocked_out_shift.clock_out, datetime)

    def test_clock_out_invalid_user(self):
        admin = create_user("admin_invalid_out", "adminpass", "admin")
        schedule = Schedule(name="Invalid ClockOut Schedule",
                            created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        staff = create_user("staff_invalid_out", "staffpass", "staff")
        start = datetime.now()
        end = start + timedelta(hours=8)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        with pytest.raises(PermissionError) as e:
            clock_out(admin.id, shift.id)
        assert str(e.value) == "Only staff can clock out"

    def test_clock_out_invalid_shift(self):
        staff = create_user("staff_invalid_shift_out", "staffpass", "staff")
        with pytest.raises(ValueError) as e:
            clock_out(staff.id, 999)
        assert str(e.value) == "Invalid shift for staff"


# Report unit tests

    def test_get_summary(self):
        admin = create_user("admin_invalid_out", "adminpass", "admin")
        db.session.add(admin)
        db.session.commit()
        
        alice = Staff("Alice", "alicepass")
        bob = Staff("Bob", "bobpass")
        db.session.add_all([alice, bob])
        db.session.commit()

        schedule = Schedule(datetime(2025, 11, 17, 8), datetime(2025, 11, 21, 16), admin.id)
        db.session.add(schedule)
        db.session.commit()
        db.session.add(schedule)
        db.session.commit()

        shift1 = Shift(staff_id=alice.id,
                       schedule_id=schedule.id,
                       start_time=datetime(2025, 11, 17, 8),
                       end_time=datetime(2025, 11, 17, 16),
                       clock_in=datetime(2025, 11, 17, 8, 5),
                       clock_out=datetime(2025, 11, 17, 16))

        shift2 = Shift(staff_id=bob.id,
                       schedule_id=schedule.id,
                       start_time=datetime(2025, 11, 17, 8),
                       end_time=datetime(2025, 11, 17, 16),
                       clock_in=datetime(2025, 11, 17, 8, 0),
                       clock_out=datetime(2025, 11, 17, 16))

        db.session.add_all([shift1, shift2])
        db.session.commit()

        summary = get_summary(schedule.id)

        assert summary["schedule_id"] == schedule.id
        assert "2025-11-17" in summary["days"]

        day_data = summary["days"]["2025-11-17"]
        assert alice.username in day_data["assigned"]
        assert bob.username in day_data["assigned"]
        assert alice.username in day_data["late"]
        assert bob.username not in day_data["late"]
        assert len(day_data["missed"]) == 0
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
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'
    })
    create_db()
    db.session.remove()
    yield app.test_client()
    db.drop_all()


def test_authenticate():
    user = User("bob", "bobpass", "user")
    assert loginCLI("bob", "bobpass") != None


class UsersIntegrationTests(unittest.TestCase):

    def test_get_all_users_json(self):
        user = create_user("bot", "bobpass", "admin")
        user = create_user("pam", "pampass", "staff")
        users_json = get_all_users_json()
        self.assertListEqual([{
            "id": 1,
            "username": "bot",
            "role": "admin"
        }, {
            "id": 2,
            "username": "pam",
            "role": "staff"
        }], users_json)

    def test_update_user(self):
        user = create_user("bot", "bobpass", "admin")
        update_user(1, "ronnie")
        user = get_user(1)
        assert user.username == "ronnie"

    def test_create_and_get_user(self):
        user = create_user("alex", "alexpass", "staff")
        retrieved = get_user(user.id)
        self.assertEqual(retrieved.username, "alex")
        self.assertEqual(retrieved.role, "staff")

    def test_get_all_users_json_integration(self):
        create_user("bot", "bobpass", "admin")
        create_user("pam", "pampass", "staff")
        users_json = get_all_users_json()
        expected = [
            {
                "id": 1,
                "username": "bot",
                "role": "admin"
            },
            {
                "id": 2,
                "username": "pam",
                "role": "staff"
            },
        ]
        self.assertEqual(users_json, expected)

    def test_admin_schedule_shift_for_staff(self):
        admin = create_user("admin1", "adminpass", "admin")
        staff = create_user("staff1", "staffpass", "staff")

        schedule = Schedule(name="Week 1 Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)
        retrieved = get_user(staff.id)

        self.assertIn(shift.id, [s.id for s in retrieved.shifts])
        self.assertEqual(shift.staff_id, staff.id)
        self.assertEqual(shift.schedule_id, schedule.id)

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

        schedule = Schedule(name="Daily Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clock_in(staff.id, shift.id)
        clock_out(staff.id, shift.id)

        updated_shift = get_shift(shift.id)
        self.assertIsNotNone(updated_shift.clock_in)
        self.assertIsNotNone(updated_shift.clock_out)
        self.assertLess(updated_shift.clock_in, updated_shift.clock_out)

    def test_admin_generate_shift_report(self):
        admin = create_user("boss", "boss123", "admin")
        staff = create_user("sam", "sampass", "staff")

        schedule = Schedule(name="Weekly Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        schedule_shift(admin.id, staff.id, schedule.id, start, end)
        report = get_shift_report(admin.id)

        self.assertTrue(any("sam" in r["staff_name"] for r in report))
        self.assertTrue(
            all("start_time" in r and "end_time" in r for r in report))

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
