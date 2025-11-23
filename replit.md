# Flask MVC Scheduling Application

## Overview
This is a Flask MVC template application for staff scheduling and roster management. The application follows the Model-View-Controller pattern and includes:
- User authentication with JWT
- Admin, staff, and user roles
- Shift scheduling and management
- Database migrations with Flask-Migrate
- Frontend with HTML templates and static files

## Technology Stack
- **Backend**: Python 3.12 + Flask 2.3.3
- **Database**: SQLite (development), PostgreSQL support available
- **Server**: Gunicorn with gevent workers
- **Authentication**: Flask-JWT-Extended
- **Testing**: pytest

## Project Structure
```
App/
├── controllers/      # Business logic
├── models/          # Database models
├── views/           # Route handlers (blueprints)
├── templates/       # HTML templates
├── static/          # CSS, JS, images
├── tests/           # Test files
└── main.py          # App factory

wsgi.py             # Application entry point + CLI commands
gunicorn_config.py  # Production server configuration
requirements.txt    # Python dependencies
```

## Setup & Configuration
- Port: 5000 (frontend)
- Database: SQLite (temp-database.db) for development
- Configuration loaded from `App/default_config.py` or environment variables

## Running the Application

### Development
The Flask app runs automatically via the configured workflow using Gunicorn on port 5000.

### Database Initialization
```bash
python3.12 -m flask init
```
This creates 4 default users (1 admin, 2 staff, 1 user).

### Running Tests
**Important**: Use `python3.12` to run Flask commands and tests:

```bash
# Run all tests
python3.12 -m pytest

# Run specific test file
python3.12 -m pytest App/tests/test_app.py

# Run user tests via Flask CLI
python3.12 -m flask test user
```

**Note**: Do not use `python3 App/tests/test_app.py` directly as it won't find the installed packages.

## Flask CLI Commands

### User Management
```bash
python3.12 -m flask user create <username> <password> <role>
python3.12 -m flask user list string
```

### Authentication
```bash
python3.12 -m flask auth login <username> <password>
python3.12 -m flask auth logout <username>
```

### Shift Management (requires login)
```bash
python3.12 -m flask shift schedule <staff_id> <schedule_id> <start> <end>
python3.12 -m flask shift roster
python3.12 -m flask shift clockin <shift_id>
python3.12 -m flask shift clockout <shift_id>
python3.12 -m flask shift report
```

### Schedule Management
```bash
python3.12 -m flask schedule create "<name>"
python3.12 -m flask schedule list
python3.12 -m flask schedule view <schedule_id>
```

## Deployment
Configured for autoscale deployment using Gunicorn. The deployment will automatically use the production-ready server configuration.

## Recent Changes (November 22, 2025)
- Updated gevent to version 24.2.1 for Python 3.12 compatibility
- Fixed syntax error in `App/controllers/user.py`
- Configured Gunicorn to use port 5000
- Set up Python 3.12 environment
- Initialized SQLite database with default users
- Configured workflow for automatic app startup
- Configured deployment settings

## Known Issues
- Test file has import error for `Report` model (model doesn't exist in codebase)
- Some tests may need updates to work with current codebase

## Default Users (after `flask init`)
1. Admin user (ID: 1)
2. Staff user (ID: 2)
3. Staff user (ID: 3)
4. Regular user (ID: 4)
