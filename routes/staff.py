from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from extensions import db
from models import Trek, Booking
from utils import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@login_required
@role_required("staff")
def dashboard():
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.created_at.desc()).all()
    return render_template("staff/dashboard.html", treks=assigned_treks)


@staff_bp.route("/treks/<int:trek_id>")
@login_required
@role_required("staff")
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff.dashboard"))

    participants = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date.desc()).all()
    return render_template("staff/trek_detail.html", trek=trek, participants=participants)


@staff_bp.route("/treks/<int:trek_id>/update", methods=["POST"])
@login_required
@role_required("staff")
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff.dashboard"))

    available_slots = request.form.get("available_slots")
    status = request.form.get("status")

    if available_slots is not None:
        available_slots = int(available_slots)
        if available_slots < 0:
            available_slots = 0
        if available_slots > trek.total_slots:
            available_slots = trek.total_slots
        trek.available_slots = available_slots

    if status in Trek.STATUS_CHOICES:
        trek.status = status

    db.session.commit()
    flash("Trek details updated.", "success")
    return redirect(url_for("staff.trek_detail", trek_id=trek.id))
