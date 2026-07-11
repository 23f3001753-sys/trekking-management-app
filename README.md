# Trekking Management Application

A role-based web application (Admin / Trek Staff / User) built with **Flask**, **Jinja2**, **Bootstrap**, and **SQLite**, for managing treks, staff assignment, and trekker bookings.

## Tech Stack
- **Backend:** Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend:** Jinja2 templates, HTML, CSS, Bootstrap 5 (via CDN)
- **Database:** SQLite (created programmatically via `db.create_all()`)

## Features

### Admin (pre-seeded, cannot self-register)
- Dashboard with total treks, users/staff, bookings, and pending approvals
- Create / edit / delete treks
- Assign approved staff to a trek
- Approve or blacklist trek staff
- Blacklist / reinstate trekkers
- View all bookings
- Search treks / staff / users by name or ID

### Trek Staff (self-register, needs admin approval)
- Dashboard of treks assigned by admin
- Update available slots and trek status (Open/Closed/Completed etc.)
- View list of trekkers registered for each assigned trek

### User / Trekker (self-register)
- Dashboard with open treks and active bookings
- Search & filter treks by difficulty / location / keyword
- Book a trek (blocked automatically once slots run out or trek isn't Open)
- Cancel a booking (slot is released back to the trek)
- View full trekking/booking history
- Edit profile (name, contact, password)

### Core safeguards
- Overbooking is prevented at the database/business-logic level
- Only the staff member assigned to a trek can manage it
- Users can only book treks with status `Open` and `available_slots > 0`
- Blacklisted users/staff are blocked from logging in
- Role-based access control decorator (`@role_required`) guards every route

## Getting Started

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app (creates trekking.db and seeds the admin automatically)
python app.py
```

The app will be available at **http://127.0.0.1:5000**

### Default Admin Login
The admin account is created automatically the first time the app runs:
- **Email:** `admin@trekking.com`
- **Password:** `Admin@123`

> Change this password (via the DB) before any real deployment.

## Project Structure
```
trekking_app/
├── app.py                 # App factory, admin seeding, login manager
├── config.py               # App configuration
├── extensions.py            # db, login_manager instances
├── models.py                # User, Trek, Booking models
├── utils.py                  # role_required decorator
├── routes/
│   ├── auth.py               # login, register, logout
│   ├── admin.py                # admin dashboard, treks, staff, users, bookings, search
│   ├── staff.py                 # staff dashboard, trek management
│   └── user.py                   # user dashboard, browse/book treks, history, profile
├── templates/                # Jinja2 templates (base + admin/staff/user/auth)
├── static/css/style.css       # Custom Bootstrap-based styling
└── requirements.txt
```

## Database Schema (ER overview)

**User** (`users`)
id, name, email, password_hash, contact, role (admin/staff/user), is_approved, is_blacklisted, created_at

**Trek** (`treks`)
id, name, location, difficulty, duration_days, total_slots, available_slots, assigned_staff_id (FK → users.id), status, start_date, end_date, description, created_at

**Booking** (`bookings`)
id, user_id (FK → users.id), trek_id (FK → treks.id), booking_date, status

Relationships:
- One **User** (staff) → many **Treks** assigned
- One **User** (trekker) → many **Bookings**
- One **Trek** → many **Bookings**
