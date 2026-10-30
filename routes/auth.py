from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import get_db_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    # Arahkan login sesuai role.
    if session.get("user_id"):
        if session.get("role") == "owner":
            return redirect(url_for("dashboard_owner"))
        elif session.get("role") == "admin":
            return redirect(url_for("dashboard_admin"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username dan password wajib diisi.", "error")
            return render_template("login.html")

        connection = None

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

            # Verifikasi password hash.
            if user and check_password_hash(user["password"], password):
                session.clear()
                session["user_id"] = user["id_user"]
                session["username"] = user["username"]
                session["role"] = user["role"]

                if user["role"] == "owner":
                    return redirect(url_for("dashboard_owner"))
                elif user["role"] == "admin":
                    return redirect(url_for("dashboard_admin"))

            flash("Username atau password salah.", "error")

        except Exception as e:
            print("Login error:", e)
            flash("Terjadi kesalahan pada sistem.", "error")

        finally:
            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))