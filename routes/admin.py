from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from extensions import db
from models import User, Trek, Booking
from utils import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role="staff", is_approved=False, is_blacklisted=False).count()

    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        pending_staff=pending_staff,
        recent_bookings=recent_bookings,
    )


# ---------------------------------------------------------------- TREKS ----

@admin_bp.route("/treks")
@login_required
@role_required("admin")
def treks():
    all_treks = Trek.query.order_by(Trek.created_at.desc()).all()
    approved_staff_list = User.query.filter_by(role="staff", is_approved=True, is_blacklisted=False).all()
    return render_template("admin/treks.html", treks=all_treks, approved_staff_list=approved_staff_list)


@admin_bp.route("/treks/new", methods=["GET", "POST"])
@login_required
@role_required("admin")
def new_trek():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        difficulty = request.form.get("difficulty", "Easy")
        duration_days = int(request.form.get("duration_days", 1) or 1)
        total_slots = int(request.form.get("total_slots", 10) or 10)
        description = request.form.get("description", "").strip()
        start_date = request.form.get("start_date") or None
        end_date = request.form.get("end_date") or None

        if not name or not location:
            flash("Trek name and location are required.", "danger")
            return redirect(url_for("admin.new_trek"))

        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration_days=duration_days,
            total_slots=total_slots,
            available_slots=total_slots,
            description=description,
            status="Pending",
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
        )
        db.session.add(trek)
        db.session.commit()
        flash("Trek created successfully.", "success")
        return redirect(url_for("admin.treks"))

    return render_template("admin/trek_form.html", trek=None)


@admin_bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":
        trek.name = request.form.get("name", trek.name).strip()
        trek.location = request.form.get("location", trek.location).strip()
        trek.difficulty = request.form.get("difficulty", trek.difficulty)
        trek.duration_days = int(request.form.get("duration_days", trek.duration_days) or trek.duration_days)

        new_total = int(request.form.get("total_slots", trek.total_slots) or trek.total_slots)
        # keep available_slots consistent when total capacity changes
        diff = new_total - trek.total_slots
        trek.total_slots = new_total
        trek.available_slots = max(0, trek.available_slots + diff)

        trek.description = request.form.get("description", trek.description).strip()
        trek.status = request.form.get("status", trek.status)

        start_date = request.form.get("start_date") or None
        end_date = request.form.get("end_date") or None
        trek.start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        trek.end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("admin.treks"))

    return render_template("admin/trek_form.html", trek=trek)


@admin_bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash("Trek removed.", "info")
    return redirect(url_for("admin.treks"))


@admin_bp.route("/treks/<int:trek_id>/assign", methods=["POST"])
@login_required
@role_required("admin")
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_id = request.form.get("staff_id")

    if staff_id:
        staff = User.query.filter_by(id=int(staff_id), role="staff", is_approved=True, is_blacklisted=False).first()
        if not staff:
            flash("Invalid staff selection.", "danger")
            return redirect(url_for("admin.treks"))
        trek.assigned_staff_id = staff.id
        if trek.status == "Pending":
            trek.status = "Approved"
        flash(f"{staff.name} assigned to '{trek.name}'.", "success")
    else:
        trek.assigned_staff_id = None
        flash("Staff unassigned from trek.", "info")

    db.session.commit()
    return redirect(url_for("admin.treks"))


# ---------------------------------------------------------------- STAFF ----

@admin_bp.route("/staff")
@login_required
@role_required("admin")
def staff_list():
    all_staff = User.query.filter_by(role="staff").order_by(User.created_at.desc()).all()
    return render_template("admin/staff.html", staff_members=all_staff)


@admin_bp.route("/staff/<int:staff_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_staff(staff_id):
    staff = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    staff.is_approved = True
    db.session.commit()
    flash(f"{staff.name} approved as Trek Staff.", "success")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/<int:staff_id>/toggle-blacklist", methods=["POST"])
@login_required
@role_required("admin")
def toggle_blacklist_staff(staff_id):
    staff = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    staff.is_blacklisted = not staff.is_blacklisted
    db.session.commit()
    state = "blacklisted" if staff.is_blacklisted else "reinstated"
    flash(f"{staff.name} has been {state}.", "warning")
    return redirect(url_for("admin.staff_list"))


# ---------------------------------------------------------------- USERS ----

@admin_bp.route("/users")
@login_required
@role_required("admin")
def users_list():
    all_users = User.query.filter_by(role="user").order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-blacklist", methods=["POST"])
@login_required
@role_required("admin")
def toggle_blacklist_user(user_id):
    user = User.query.filter_by(id=user_id, role="user").first_or_404()
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    state = "blacklisted" if user.is_blacklisted else "reinstated"
    flash(f"{user.name} has been {state}.", "warning")
    return redirect(url_for("admin.users_list"))


# ------------------------------------------------------------- BOOKINGS ----

@admin_bp.route("/bookings")
@login_required
@role_required("admin")
def bookings_list():
    all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin/bookings.html", bookings=all_bookings)


# --------------------------------------------------------------- SEARCH ----

@admin_bp.route("/search")
@login_required
@role_required("admin")
def search():
    query = request.args.get("q", "").strip()
    search_type = request.args.get("type", "trek")

    results = []
    if query:
        if search_type == "trek":
            like = f"%{query}%"
            results = Trek.query.filter(
                db.or_(Trek.name.ilike(like), Trek.location.ilike(like), Trek.id == query if query.isdigit() else False)
            ).all()
        elif search_type == "staff":
            like = f"%{query}%"
            results = User.query.filter(
                User.role == "staff",
                db.or_(User.name.ilike(like), User.email.ilike(like), User.id == query if query.isdigit() else False),
            ).all()
        elif search_type == "user":
            like = f"%{query}%"
            results = User.query.filter(
                User.role == "user",
                db.or_(User.name.ilike(like), User.email.ilike(like), User.id == query if query.isdigit() else False),
            ).all()

    return render_template("admin/search.html", results=results, query=query, search_type=search_type)
