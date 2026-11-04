
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from database import get_db_connection

jenis_kendaraan_bp = Blueprint("jenis_kendaraan", __name__)

# Batasi akses hanya untuk Owner.
def owner_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("auth.login"))

        if session.get("role") != "owner":
            flash("Kamu tidak memiliki akses ke halaman ini.", "error")
            # Jika Admin mencoba akses, arahkan ke dashboard admin.
            if session.get("role") == "admin":
                return redirect(url_for("dashboard_admin"))
            return redirect(url_for("auth.login"))

        return function(*args, **kwargs)

    return wrapper


# Tampilkan daftar jenis kendaraan.
@jenis_kendaraan_bp.route("/")
@owner_required
def daftar_jenis_kendaraan():
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_jenis_kendaraan, jenis_kendaraan, status
            FROM Jenis_Kendaraan
            ORDER BY jenis_kendaraan ASC
        """)

        daftar = cursor.fetchall()
        cursor.close()

        return render_template(
            "owner/jenis_kendaraan.html",
            daftar_jenis_kendaraan=daftar,
            jenis_kendaraan_edit=None
        )

    except Exception as e:
        print("Error menampilkan jenis kendaraan:", e)
        flash("Gagal mengambil data jenis kendaraan.", "error")

        return render_template(
            "owner/jenis_kendaraan.html",
            daftar_jenis_kendaraan=[],
            jenis_kendaraan_edit=None
        )

    finally:
        if connection and connection.is_connected():
            connection.close()


# Tambahkan jenis kendaraan.
@jenis_kendaraan_bp.route("/tambah", methods=["POST"])
@owner_required
def tambah_jenis_kendaraan():
    nama = request.form.get("jenis_kendaraan", "").strip()

    if not nama:
        flash("Jenis kendaraan wajib diisi.", "error")
        return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))

    if len(nama) > 20:
        flash("Nama jenis kendaraan maksimal 20 karakter.", "error")
        return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO Jenis_Kendaraan (jenis_kendaraan)
            VALUES (%s)
        """, (nama,))

        connection.commit()
        cursor.close()

        flash("Jenis kendaraan berhasil ditambahkan.", "success")

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error tambah jenis kendaraan:", e)

        if getattr(e, "errno", None) == 1062:
            flash("Jenis kendaraan sudah terdaftar.", "error")
        else:
            flash("Gagal menambahkan jenis kendaraan.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))


# Tampilkan form edit jenis kendaraan.
@jenis_kendaraan_bp.route("/edit/<int:id_jenis_kendaraan>")
@owner_required
def edit_jenis_kendaraan(id_jenis_kendaraan):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

# Ambil data jenis kendaraan yang akan diedit.
        cursor.execute("""
            SELECT id_jenis_kendaraan, jenis_kendaraan, status
            FROM Jenis_Kendaraan
            WHERE id_jenis_kendaraan = %s
        """, (id_jenis_kendaraan,))
        jenis_edit = cursor.fetchone()

        if not jenis_edit:
            cursor.close()
            flash("Jenis kendaraan tidak ditemukan.", "error")
            return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))

        # Ambil seluruh daftar jenis kendaraan menggunakan cursor yang sama.
        cursor.execute("""
            SELECT id_jenis_kendaraan, jenis_kendaraan, status
            FROM Jenis_Kendaraan
            ORDER BY jenis_kendaraan ASC
        """)
        daftar = cursor.fetchall()
        cursor.close()

        return render_template(
            "owner/jenis_kendaraan.html",
            daftar_jenis_kendaraan=daftar,
            jenis_kendaraan_edit=jenis_edit
        )

    except Exception as e:
        print("Error mengambil data edit:", e)
        flash("Gagal mengambil data jenis kendaraan.", "error")
        return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))

    finally:
        if connection and connection.is_connected():
            connection.close()


# Simpan perubahan nama jenis kendaraan.
@jenis_kendaraan_bp.route("/edit/<int:id_jenis_kendaraan>", methods=["POST"])
@owner_required
def simpan_edit_jenis_kendaraan(id_jenis_kendaraan):
    nama = request.form.get("jenis_kendaraan", "").strip()

    if not nama:
        flash("Jenis kendaraan wajib diisi.", "error")
        return redirect(url_for("jenis_kendaraan.edit_jenis_kendaraan", id_jenis_kendaraan=id_jenis_kendaraan))

    if len(nama) > 20:
        flash("Nama jenis kendaraan maksimal 20 karakter.", "error")
        return redirect(url_for("jenis_kendaraan.edit_jenis_kendaraan", id_jenis_kendaraan=id_jenis_kendaraan))

    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Jenis_Kendaraan
            SET jenis_kendaraan = %s
            WHERE id_jenis_kendaraan = %s
        """, (nama, id_jenis_kendaraan))

        if cursor.rowcount == 0:
            cursor.execute("""
                SELECT id_jenis_kendaraan
                FROM Jenis_Kendaraan
                WHERE id_jenis_kendaraan = %s
            """, (id_jenis_kendaraan,))

            if not cursor.fetchone():
                flash("Jenis kendaraan tidak ditemukan.", "error")
            else:
                flash("Tidak ada perubahan nama jenis kendaraan.", "info")
        else:
            connection.commit()
            flash("Jenis kendaraan berhasil diperbarui.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()
        print("Error edit jenis kendaraan:", e)

        if getattr(e, "errno", None) == 1062:
            flash("Nama jenis kendaraan sudah digunakan.", "error")
        else:
            flash("Gagal memperbarui jenis kendaraan.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))


# Nonaktifkan jenis kendaraan.
@jenis_kendaraan_bp.route("/nonaktifkan/<int:id_jenis_kendaraan>", methods=["POST"])
@owner_required
def nonaktifkan_jenis_kendaraan(id_jenis_kendaraan):
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Jenis_Kendaraan
            SET status = 'nonaktif'
            WHERE id_jenis_kendaraan = %s
              AND status = 'aktif'
        """, (id_jenis_kendaraan,))

        if cursor.rowcount == 0:
            flash("Jenis kendaraan tidak ditemukan atau sudah nonaktif.", "error")
        else:
            connection.commit()
            flash("Jenis kendaraan berhasil dinonaktifkan.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error nonaktifkan jenis kendaraan:", e)
        flash("Gagal menonaktifkan jenis kendaraan.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))


# Aktifkan kembali jenis kendaraan.
@jenis_kendaraan_bp.route("/aktifkan/<int:id_jenis_kendaraan>", methods=["POST"])
@owner_required
def aktifkan_jenis_kendaraan(id_jenis_kendaraan):
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Jenis_Kendaraan
            SET status = 'aktif'
            WHERE id_jenis_kendaraan = %s
              AND status = 'nonaktif'
        """, (id_jenis_kendaraan,))

        if cursor.rowcount == 0:
            flash("Jenis kendaraan tidak ditemukan atau sudah aktif.", "error")
        else:
            connection.commit()
            flash("Jenis kendaraan berhasil diaktifkan kembali.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error aktifkan jenis kendaraan:", e)
        flash("Gagal mengaktifkan jenis kendaraan.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("jenis_kendaraan.daftar_jenis_kendaraan"))
