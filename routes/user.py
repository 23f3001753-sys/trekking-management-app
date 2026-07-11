from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from extensions import db
from models import Trek, Booking
from utils import role_required

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/dashboard")
@login_required
@role_required("user")
def dashboard():
    open_treks = Trek.query.filter_by(status="Open").order_by(Trek.start_date.asc()).limit(6).all()
    my_bookings = (
        Booking.query.filter_by(user_id=current_user.id, status="Booked")
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template("user/dashboard.html", open_treks=open_treks, my_bookings=my_bookings)


@user_bp.route("/treks")
@login_required
@role_required("user")
def browse_treks():
    query = Trek.query.filter(Trek.status.in_(["Open", "Closed"]))

    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "").strip()
    keyword = request.args.get("q", "").strip()

    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))
    if keyword:
        query = query.filter(Trek.name.ilike(f"%{keyword}%"))

    treks = query.order_by(Trek.start_date.asc()).all()

    booked_trek_ids = {
        b.trek_id for b in Booking.query.filter_by(user_id=current_user.id, status="Booked").all()
    }

    return render_template(
        "user/treks.html",
        treks=treks,
        booked_trek_ids=booked_trek_ids,
        difficulty=difficulty,
        location=location,
        keyword=keyword,
    )


@user_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@login_required
@role_required("user")
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != "Open":
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for("user.browse_treks"))

    if trek.available_slots <= 0:
        flash("No slots available for this trek.", "danger")
        return redirect(url_for("user.browse_treks"))

    existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id, status="Booked").first()
    if existing:
        flash("You have already booked this trek.", "warning")
        return redirect(url_for("user.browse_treks"))

    booking = Booking(user_id=current_user.id, trek_id=trek.id, status="Booked")
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()

    flash(f"Successfully booked '{trek.name}'!", "success")
    return redirect(url_for("user.dashboard"))


@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
@role_required("user")
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()

    if booking.status == "Booked":
        booking.status = "Cancelled"
        booking.trek.available_slots += 1
        db.session.commit()
        flash("Booking cancelled.", "info")
    else:
        flash("This booking cannot be cancelled.", "warning")

    return redirect(url_for("user.history"))


@user_bp.route("/history")
@login_required
@role_required("user")
def history():
    all_bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template("user/history.html", bookings=all_bookings)


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("user")
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.contact = request.form.get("contact", current_user.contact).strip()

        new_password = request.form.get("password", "").strip()
        if new_password:
            current_user.set_password(new_password)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("user.profile"))

    return render_template("user/profile.html")
