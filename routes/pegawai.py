from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from database import get_db_connection

pegawai_bp = Blueprint("pegawai", __name__)

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


# Tampilkan daftar pegawai.
@pegawai_bp.route("/")
@owner_required
def daftar_pegawai():
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_pegawai, nama, status
            FROM Pegawai
            ORDER BY nama ASC
        """)

        daftar = cursor.fetchall()
        cursor.close()

        return render_template(
            "owner/pegawai.html",
            daftar_pegawai=daftar,
            pegawai_edit=None
        )

    except Exception as e:
        print("Error menampilkan pegawai:", e)
        flash("Gagal mengambil data pegawai.", "error")
        return render_template(
            "owner/pegawai.html",
            daftar_pegawai=[],
            pegawai_edit=None
        )

    finally:
        if connection and connection.is_connected():
            connection.close()


# Tampilkan pegawai baru.
@pegawai_bp.route("/tambah", methods=["POST"])
@owner_required
def tambah_pegawai():
    nama = request.form.get("nama", "").strip()

    if not nama:
        flash("Nama pegawai wajib diisi.", "error")
        return redirect(url_for("pegawai.daftar_pegawai"))

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO Pegawai (nama)
            VALUES (%s)
        """

        cursor.execute(query, (nama,))
        connection.commit()

        flash("Pegawai berhasil ditambahkan.", "success")
        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error tambah pegawai:", e)

        if getattr(e, "errno", None) == 1062:
            flash("Nama pegawai sudah terdaftar.", "error")
        else:
            flash("Gagal menambahkan pegawai.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("pegawai.daftar_pegawai"))


# Tampilkan form edit pegawai.
@pegawai_bp.route("/edit/<int:id_pegawai>")
@owner_required
def edit_pegawai(id_pegawai):
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

# Ambil data pegawai yang akan diedit.
        cursor.execute("""
            SELECT id_pegawai, nama, status
            FROM Pegawai
            WHERE id_pegawai = %s
        """, (id_pegawai,))
        pegawai = cursor.fetchone()

        if not pegawai:
            cursor.close()
            flash("Data pegawai tidak ditemukan.", "error")
            return redirect(url_for("pegawai.daftar_pegawai"))

        # Ambil seluruh daftar pegawai menggunakan cursor yang sama.
        cursor.execute("""
            SELECT id_pegawai, nama, status
            FROM Pegawai
            ORDER BY nama ASC
        """)
        daftar = cursor.fetchall()
        cursor.close()

        return render_template(
            "owner/pegawai.html",
            daftar_pegawai=daftar,
            pegawai_edit=pegawai
        )

    except Exception as e:
        print("Error mengambil data edit:", e)
        flash("Gagal mengambil data pegawai.", "error")
        return redirect(url_for("pegawai.daftar_pegawai"))

    finally:
        if connection and connection.is_connected():
            connection.close()


# Simpan perubahan nama pegawai.
@pegawai_bp.route("/edit/<int:id_pegawai>", methods=["POST"])
@owner_required
def simpan_edit_pegawai(id_pegawai):
    nama = request.form.get("nama", "").strip()

    if not nama:
        flash("Nama pegawai wajib diisi.", "error")
        return redirect(url_for("pegawai.edit_pegawai", id_pegawai=id_pegawai))

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Pegawai
            SET nama = %s
            WHERE id_pegawai = %s
        """, (nama, id_pegawai))

        if cursor.rowcount == 0:
            flash("Data pegawai tidak ditemukan atau tidak ada perubahan.", "error")
        else:
            connection.commit()
            flash("Nama pegawai berhasil diperbarui.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error edit pegawai:", e)

        if getattr(e, "errno", None) == 1062:
            flash("Nama pegawai sudah digunakan.", "error")
        else:
            flash("Gagal memperbarui data pegawai.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("pegawai.daftar_pegawai"))


# Nonaktifkan pegawai.
@pegawai_bp.route("/nonaktifkan/<int:id_pegawai>", methods=["POST"])
@owner_required
def nonaktifkan_pegawai(id_pegawai):
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Pegawai
            SET status = 'nonaktif'
            WHERE id_pegawai = %s
              AND status = 'aktif'
        """, (id_pegawai,))

        if cursor.rowcount == 0:
            flash("Pegawai tidak ditemukan atau sudah nonaktif.", "error")
        else:
            connection.commit()
            flash("Pegawai berhasil dinonaktifkan.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error nonaktifkan pegawai:", e)
        flash("Gagal menonaktifkan pegawai.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("pegawai.daftar_pegawai"))


# Aktifkan kembali pegawai.
@pegawai_bp.route("/aktifkan/<int:id_pegawai>", methods=["POST"])
@owner_required
def aktifkan_pegawai(id_pegawai):
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Pegawai
            SET status = 'aktif'
            WHERE id_pegawai = %s
              AND status = 'nonaktif'
        """, (id_pegawai,))

        if cursor.rowcount == 0:
            flash("Pegawai tidak ditemukan atau sudah aktif.", "error")
        else:
            connection.commit()
            flash("Pegawai berhasil diaktifkan kembali.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error mengaktifkan pegawai:", e)
        flash("Gagal mengaktifkan kembali pegawai.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("pegawai.daftar_pegawai"))