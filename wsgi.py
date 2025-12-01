import click, pytest, sys, os
from flask.cli import with_appcontext, AppGroup
from datetime import datetime
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from datetime import datetime

from App.database import db, get_migrate
from App.models import User
from App.main import create_app 
from App.controllers import (
    create_user, get_all_users_json, get_all_users, initialize, clock_in, clock_out, view_report, login,loginCLI
)
from App.controllers.admin import schedule_shift
from App.models.schedule import Schedule
from App.models.shift import Shift
from App.controllers.user import get_all_users_by_role
from App.services.strategies.even_scheduler import EvenScheduler
from App.services.strategies.minimum_scheduler import MinimumScheduler
from App.services.strategies.day_night_scheduler import DayNightScheduler


app = create_app()
migrate = get_migrate(app)

@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('database intialized')

auth_cli = AppGroup('auth', help='Authentication commands')

@auth_cli.command("login", help="Login and get JWT token")
@click.argument("username")
@click.argument("password")
def login_command(username, password):
    result = loginCLI(username, password)
    if result["message"] == "Login successful":
        token = result["token"]
        with open("active_token.txt", "w") as f:
            f.write(token)
        print(f"✅ {result['message']}! JWT token saved for CLI use.")
    else:
        print(f"⚠️ {result['message']}")

@auth_cli.command("logout", help="Logout a user by username")
@click.argument("username")
def logout_command(username):
    from App.controllers.auth import logout
    result = logout(username)
    if os.path.exists("active_token.txt"):
        os.remove("active_token.txt")
    print(result["message"])
    
app.cli.add_command(auth_cli)


user_cli = AppGroup('user', help='User object commands') 

@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
@click.argument("role", default="staff")
def create_user_command(username, password, role):
    create_user(username, password, role)
    print(f'{username} created!')

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())

app.cli.add_command(user_cli)



shift_cli = AppGroup('shift', help='Shift management commands')

@shift_cli.command("schedule", help="Admin schedules a shift or uses a strategy")
@click.argument("mode")  # "manual" or "strategy"
@click.argument("args", nargs=-1)  # flexible args
def schedule_shift_command(mode, args):
    from datetime import datetime
    from App.database import db
    from App.models.schedule import Schedule
    from App.models.shift import Shift
    from App.controllers.user import get_all_users_by_role
    from App.services.strategies.even_scheduler import EvenScheduler
    from App.services.strategies.minimum_scheduler import MinimumScheduler
    from App.services.strategies.day_night_scheduler import DayNightScheduler

    admin = require_admin_login()

    if mode == "manual":
        if len(args) != 4:
            print("❌ Usage: flask shift schedule manual <staff_id> <schedule_id> <start_iso> <end_iso>")
            return

        staff_id, schedule_id, start, end = args
        start_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end)

        # manual assignment controller
        shift = schedule_shift(admin.id, int(staff_id), int(schedule_id), start_time, end_time)

        db.session.add(shift)
        db.session.commit()

        print(f"✅ Shift scheduled under Schedule {schedule_id} by {admin.username}")
        print(shift.get_json())

    elif mode == "strategy":
        if len(args) != 3:
            print("❌ Usage: flask shift schedule strategy <even|min|daynight> <start_date_iso> <end_date_iso>")
            return

        strategy_name, start_date, end_date = args
        staff_list = get_all_users_by_role("staff")

        # create empty schedule
        schedule = Schedule(
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date),
            admin_id=admin.id
        )

        # pick strategy
        strategy_name = strategy_name.lower()
        if strategy_name == "even":
            strategy = EvenScheduler()
        elif strategy_name == "minimum":
            strategy = MinimumScheduler()
        elif strategy_name == "daynight":
            strategy = DayNightScheduler()
        else:
            print("❌ Invalid strategy. Use: even, minimum, daynight")
            return

        # fill schedule using strategy
        strategy.fill_schedule(staff_list, schedule)

        db.session.add(schedule)
        db.session.commit()

        print(f"✅ Schedule created with {strategy_name} strategy by {admin.username}")
        print(schedule.get_json())

app.cli.add_command(shift_cli)

@shift_cli.command("roster", help="Staff views combined roster")
@click.argument("schedule_id", type=int)
def roster_command(schedule_id):
    staff = require_staff_login()
    from App.controllers import viewSchedule

    roster = viewSchedule(staff.id, schedule_id)
    print(f"📋 Roster for Schedule {schedule_id}:")
    print(roster)

app.cli.add_command(shift_cli)

@shift_cli.command("clockin", help="Staff clocks in")
@click.argument("shift_id", type=int)
def clockin_command(shift_id):
    staff = require_staff_login()
    try:
        shift = clock_in(staff.id, shift_id)
        print(f"🕒 {staff.username} clocked in: {shift.get_json()}")
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")


@shift_cli.command("clockout", help="Staff clocks out")
@click.argument("shift_id", type=int)
def clockout_command(shift_id):
    staff = require_staff_login()
    try:
        shift = clock_out(staff.id, shift_id)
        print(f"🕕 {staff.username} clocked out: {shift.get_json()}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")


app.cli.add_command(shift_cli)

schedule_cli = AppGroup('schedule', help='Schedule management commands')

@schedule_cli.command("assign", help="Admin assigns staff member to an existing shift")
@click.argument("shift_id", type=int)
@click.argument("staff_id", type=int)
def assign_shift_command(shift_id, staff_id):
    from App.models.shift import Shift
    from App.controllers import get_user
    admin = require_admin_login()
    
    shift = Shift.get_shift(shift_id)
    
    if not shift:
        print(f"❌ Shift {shift_id} not found.")
        return
    
    staff = get_user(staff_id)
    if not staff or staff.role.lower() != "staff":
        print(f"❌ User {staff_id} is not a staff member.")
        return
    
    try:
        shift.assignStaff(staff)
        shift.updateStatus()  
        db.session.commit()
        print(f"✅ {staff.username} assigned to shift {shift.id} by {admin.username}.")
    except Exception as e:
        print(f"❌ Assignment failed: {e}")
        
app.cli.add_command(schedule_cli)


@shift_cli.command("report", help="Admin views shift report summary")
@click.argument("schedule_id", type=int)
def report_command(scheduleID):
    admin = require_admin_login()
    try:
        report = view_report(scheduleID, admin.id)
        print(f"📊 Shift report summary:")
        print(report)
    except Exception as e:
        print(f"❌ Report could not be viewed: {e}")
    

app.cli.add_command(shift_cli)

shift_cli = AppGroup('shift', help='Shift management commands')

@shift_cli.command("view", help="Staff views their shifts for a schedule")
@click.argument("schedule_id", type=int)
def view_shifts_command(schedule_id):
    staff = require_staff_login()
    from App.controllers import viewShifts

    shifts = viewShifts(staff.id, schedule_id)
    print(f"📋 Shifts for {staff.username} in Schedule {schedule_id}:")
    
    if not shifts:
        print("No shifts found.")
        return
    
    for s in shifts:
        print(f"- Shift ID {s['id']}")
        print(f"  Start Time: {s['start_time']}")
        print(f"  End Time: {s['end_time']}")
        print(f"  Clock In: {s['clock_in']}")
        print(f"  Clock Out: {s['clock_out']}")
        print("")
        
app.cli.add_command(shift_cli)

def require_admin_login():
    import os
    from flask_jwt_extended import decode_token
    from App.controllers import get_user

    if not os.path.exists("active_token.txt"):
        raise PermissionError("⚠️ No active session. Please login first.")

    with open("active_token.txt", "r") as f:
        token = f.read().strip()

    try:
        decoded = decode_token(token)
        user_id = decoded["sub"]
        user = get_user(user_id)
        if not user or user.role != "admin":
            raise PermissionError("🚫 Only an admin can use this command.")
        return user
    except Exception as e:
        raise PermissionError(f"Invalid or expired token. Please login again. ({e})")

def require_staff_login():
    import os
    from flask_jwt_extended import decode_token
    from App.controllers import get_user

    if not os.path.exists("active_token.txt"):
        raise PermissionError("⚠️ No active session. Please login first.")

    with open("active_token.txt", "r") as f:
        token = f.read().strip()

    try:
        decoded = decode_token(token)
        user_id = decoded["sub"]
        user = get_user(user_id)
        if not user or user.role != "staff":
            raise PermissionError("🚫 Only staff can use this command.")
        return user
    except Exception as e:
        raise PermissionError(f"Invalid or expired token. Please login again. ({e})")

schedule_cli = AppGroup('schedule', help='Schedule management commands')

    
@schedule_cli.command("list", help="List all schedules")
def list_schedules_command():
    from App.models import Schedule
    admin = require_admin_login()
    schedules = Schedule.query.all()
    print(f"✅ Found {len(schedules)} schedule(s):")
    for s in schedules:
        print(s.get_json())


@schedule_cli.command("view", help="View a schedule and its shifts")
@click.argument("schedule_id", type=int)
def view_schedule_command(schedule_id):
    from App.models import Schedule
    admin = require_admin_login()
    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        print("⚠️ Schedule not found.")
    else:
        print(f"✅ Viewing schedule {schedule_id}:")
        print(schedule.get_json())

app.cli.add_command(schedule_cli)
'''
Test Commands
'''
test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    
app.cli.add_command(test)
