from flask import Flask, redirect, url_for, session, render_template, flash
from functools import wraps
from dotenv import load_dotenv
import os

from routes.auth import auth_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Route login dan logout.
app.register_blueprint(auth_bp)


# Middleware batasi akses berdasarkan login dan role.
def login_required(role=None):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            # User sudah login?
            if not session.get("user_id"):
                flash("Login terlebih dahulu untuk mengakses halaman ini!", "error")
                return redirect(url_for("auth.login"))

            # Cek role user.
            if role and session.get("role") != role:
                flash("Akses ditolak!", "error")
                return redirect(url_for("auth.login"))

            return function(*args, **kwargs)

        return wrapper
    return decorator


# Dashboard Owner
@app.route("/owner/dashboard")
@login_required(role="owner")
def dashboard_owner():
    return render_template("dashboard_owner.html")


# Dashboard Admin
@app.route("/admin/dashboard")
@login_required(role="admin")
def dashboard_admin():
    return render_template("dashboard_admin.html")


if __name__ == "__main__":
    app.run(debug=True)