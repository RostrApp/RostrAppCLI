# ✏️ RostrApp 
RostrApp is a CLI shift-scheduling and rostering app with API endpoints for administrators and staff to manage schedules, assign shifts, generate reports and track attendance.

Staff can view their assigned shifts, clock in/out and access shift reports while admins can create schedules manually or using built-in scheduling strategies:
* Even Scheduling
> Distributes shifts evenly across all staff so that everyone works roughly the same number of shifts.
* Minimum Scheduling
> Distributes shifts to minimize the number of working days per staff member.
* Day/Night Scheduling
> Splits days into day shifts and night shifts and assigns them to staff members.


## 🚀 Setup
### Install dependencies:
```bash
$ pip install -r requirements.txt
```

### Initialise the database:
```bash
$ flask init
```
This creates all tables and performs initial setup along with 3 users:
* Admin
    * ID: 1
    * Username: bob
    * Password: bobpass
* Staff
    * ID: 2
    * Username: jane
    * Password: janepass
* Admin
    * ID: 3
    * Username: alice
    * Password: alicepass

## 🔐 Authentication Commands (`flask auth`)

#### Login
```bash
flask auth login <username> <password>
```
If successful, a JWT token is saved to `active_token.txt` and will be used by all protected commands.

#### Logout
```bash
flask auth logout <username>
```
Ends user session and removes active_token.txt.

## 👤 User Management (`flask user`)

#### Create a user
```bash
flask user create <username> <password> <role>
```
Roles can either be admin, staff or user.

#### List all users
```bash
flask user list string
flask user list json
```

## 🗓️ Schedule Commands (`flask schedule`)

##### Assign staff to an existing shift (Admin only)
```bash
flask schedule assign <shift_id> <staff_id>
```

#### List All Schedules (Admin only)
```bash
flask schedule list 
```

#### View a specific Schedule (Admin only)
```bash
flask schedule view <schedule_id>
```

## ⏱️ Shift Commands (`flask shift`)

#### Schedule all Staff using a Scheduling Strategy
```bash
flask shift schedule strategy <even|min|daynight> <start_iso> <end_iso>
```

#### Manually add new Shift to Schedule (Admin only)
Format the start and end times in ISO
For example, enter 2025-01-02T08:00:00 for 2nd January, 2025 at 8:00am
```bash
flask shift schedule manual <staff_id> <schedule_id> <start_iso> <end_iso>
```

#### View Entire Roster (Staff only)
```bash
flask shift roster <schedule_id>
```

#### View Personal Shifts (Staff only)
```bash
flask shift view <schedule_id>
```

#### Clock in to Shift (Staff only)
```bash
flask shift clockin <shift_id>
```

#### Clock out of Shift (Staff only)
```bash
flask shift clockout <shift_id>
```

#### View Weekly Shift Report (Admin only)
```bash
flask shift report <schedule_id>
```

## 🧪 Testing Commands (`flask test`)
```bash
flask test user <unit|int|all>
```
Enter `flask test user` to execute all tests.
Add `unit` or `int` at the end of the command to execute only unit or integration tests.


