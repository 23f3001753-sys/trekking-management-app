from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    """Unified user table for Admin, Trek Staff and Trekkers (Users)."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(50))

    # role: 'admin', 'staff', 'user'
    role = db.Column(db.String(20), nullable=False, default="user")

    # Staff must be approved by Admin before they can access their dashboard.
    is_approved = db.Column(db.Boolean, default=False)

    # Admin can blacklist staff or users.
    is_blacklisted = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Treks assigned to this user, if role == 'staff'
    treks_assigned = db.relationship(
        "Trek", backref="staff", lazy=True, foreign_keys="Trek.assigned_staff_id"
    )
    # Bookings made by this user, if role == 'user'
    bookings = db.relationship(
        "Booking", backref="user", lazy=True, foreign_keys="Booking.user_id"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        # Overrides flask-login's UserMixin.is_active:
        # blacklisted users/staff cannot log in / stay logged in.
        return not self.is_blacklisted

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Trek(db.Model):
    __tablename__ = "treks"

    STATUS_CHOICES = ["Pending", "Approved", "Open", "Closed", "Completed"]
    DIFFICULTY_CHOICES = ["Easy", "Moderate", "Hard"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="Easy")
    duration_days = db.Column(db.Integer, nullable=False, default=1)

    total_slots = db.Column(db.Integer, nullable=False, default=10)
    available_slots = db.Column(db.Integer, nullable=False, default=10)

    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="Pending")
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship(
        "Booking", backref="trek", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def booked_count(self):
        return sum(1 for b in self.bookings if b.status == "Booked")

    def __repr__(self):
        return f"<Trek {self.name}>"


class Booking(db.Model):
    __tablename__ = "bookings"

    STATUS_CHOICES = ["Booked", "Cancelled", "Completed"]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default="Booked")

    def __repr__(self):
        return f"<Booking user={self.user_id} trek={self.trek_id} status={self.status}>"
