from flask import Flask, render_template, redirect, url_for
from flask_login import current_user

from config import Config
from extensions import db, login_manager
from models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.staff import staff_bp
    from routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif current_user.role == "staff":
                return redirect(url_for("staff.dashboard"))
            else:
                return redirect(url_for("user.dashboard"))
        return render_template("index.html")

    with app.app_context():
        db.create_all()
        seed_admin()

    return app


def seed_admin():
    """Programmatically create the pre-existing Admin account if absent."""
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            name="System Admin",
            email="admin@trekking.com",
            role="admin",
            is_approved=True,
            is_blacklisted=False,
            contact="N/A",
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()
        print("Seeded default admin -> email: admin@trekking.com  password: Admin@123")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
