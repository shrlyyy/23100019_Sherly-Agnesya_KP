from flask import Flask, redirect, url_for, session, render_template, flash
from functools import wraps
from dotenv import load_dotenv
import os

from routes.auth import auth_bp
from routes.pegawai import pegawai_bp
from routes.jenis_kendaaan import jenis_kendaraan_bp
from routes.layanan_harga import layanan_harga_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Route login dan logout.
app.register_blueprint(auth_bp)

# Route CRUD data pegawai oleh Owner.
app.register_blueprint(
    pegawai_bp,
    url_prefix = "/owner/pegawai"
)

# Route CRUD data jenis kendaraan oleh Owner.
app.register_blueprint(
    jenis_kendaraan_bp,
    url_prefix = "/owner/jenis-kendaraan"
)

# Route CRUD data jenis layanan dan harga oleh Owner.
app.register_blueprint(
    layanan_harga_bp,
    url_prefix = "/owner/layanan-dan-harga"
)


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