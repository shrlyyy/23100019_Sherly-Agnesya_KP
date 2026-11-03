
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import get_db_connection

auth_bp = Blueprint("auth", __name__)

# Fitur login pakai get untuk buka halaman, post waktu login.
@auth_bp.route("/", methods=["GET", "POST"])
def login():

    # Arahkan pengguna yang sudah login sesuai role.
    if session.get("user_id"):
        if session.get("role") == "owner":
            return redirect(url_for("dashboard_owner")) # Kalau udah login.
        elif session.get("role") == "admin":
            return redirect(url_for("dashboard_admin")) # Kalau udah login.

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Validasi input
        if not username and not password:
            flash("Username dan password wajib diisi.", "error")
            return render_template("login.html")

        if not username:
            flash("Username wajib diisi.", "error")
            return render_template("login.html")

        if not password:
            flash("Password wajib diisi.", "error")
            return render_template("login.html")

        connection = None

# Cari ke database.
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT id_user, username, password, role
                FROM User
                WHERE username = %s
                LIMIT 1
            """

            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()

            # Periksa username.
            if not user:
                flash("Username salah.", "error")
                return render_template("login.html")

            # Periksa password.
            if not check_password_hash(user["password"], password):
                flash("Password salah.", "error")
                return render_template("login.html")

            # Login berhasil.
            session.clear()
            session["user_id"] = user["id_user"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            # Arahkan ke halaman masing-masing jika berhasil.
            if user["role"] == "owner":
                return redirect(url_for("dashboard_owner"))

            elif user["role"] == "admin":
                return redirect(url_for("dashboard_admin"))

            flash("Role pengguna tidak dikenali.", "error")

        except Exception as e:
            print("Login error:", e)
            flash("Terjadi kesalahan saat mengakses database.", "error")

        finally:
            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
