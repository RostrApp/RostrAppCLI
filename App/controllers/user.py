from App.models import User, Admin, Staff, Shift
from App.database import db

VALID_ROLES = {"user", "staff", "admin"}

def create_user(username, password, role):
    role = role.lower().strip()
    if role not in VALID_ROLES:
        print(f"⚠️ Invalid role '{role}'. Must be one of {VALID_ROLES}")
        return None
    if role == "admin":
        newuser = Admin(username=username, password=password)
    elif role == "staff":
        newuser = Staff(username=username, password=password)
    else:
        newuser = User(username=username, password=password, role="user")

    db.session.add(newuser)
    db.session.commit()
    return newuser

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_user(id):
    return db.session.get(User, id)

def get_all_users():
    return User.query.all()

def get_all_users_json():
    users = get_all_users()
    if not users:
        return []
    return [user.get_json() for user in users]

#added method for scheduling purposes
def get_all_users_by_role(role):
    return User.query.filter_by(role=role).all()

def get_all_users_by_role_json(role):
    users = get_all_users_by_role(role)
    if not users:
        return []
    return [user.get_json() for user in users]

def update_user(id, username):
    user = get_user(id)
    if user:
        user.username = username
        db.session.commit()
        return user
    return None

#not sure if this method should be added here
def get_all_shifts()
    return Shift.query.all()
