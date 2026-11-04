from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from database import get_db_connection

layanan_harga_bp = Blueprint("layanan_harga", __name__)

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


# Ambil jenis kendaraan yang masih aktif.
def get_jenis_kendaraan(cursor):
    cursor.execute("""
        SELECT id_jenis_kendaraan, jenis_kendaraan
        FROM Jenis_Kendaraan
        WHERE status = 'aktif'
        ORDER BY jenis_kendaraan ASC
    """)
    return cursor.fetchall()


# Tampilkan halaman layanan dan harga.
@layanan_harga_bp.route("/")
@owner_required
def daftar_layanan():
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        jenis_kendaraan = get_jenis_kendaraan(cursor)

        cursor.execute("""
            SELECT
                jl.id_jenis_layanan,
                jl.nama_layanan,
                jl.status,
                h.id_jenis_kendaraan,
                h.harga
            FROM Jenis_Layanan jl
            LEFT JOIN Harga h
                ON jl.id_jenis_layanan = h.id_jenis_layanan
            ORDER BY jl.nama_layanan ASC
        """)

        rows = cursor.fetchall()

        # Menggabungkan data harga berdasarkan layanan.
        layanan_dict = {}

        for row in rows:
            id_layanan = row["id_jenis_layanan"]

            if id_layanan not in layanan_dict:
                layanan_dict[id_layanan] = {
                    "id_jenis_layanan": id_layanan,
                    "nama_layanan": row["nama_layanan"],
                    "status": row["status"],
                    "harga": {}
                }

            if row["id_jenis_kendaraan"] is not None:
                layanan_dict[id_layanan]["harga"][
                    row["id_jenis_kendaraan"]
                ] = row["harga"]

        daftar = list(layanan_dict.values())
        cursor.close()

        return render_template(
            "owner/layanan_harga.html",
            daftar_layanan=daftar,
            jenis_kendaraan=jenis_kendaraan,
            layanan_edit=None,
            harga_edit={}
        )

    except Exception as e:
        print("Error menampilkan layanan:", e)
        flash("Gagal mengambil data layanan dan harga.", "error")
        return redirect(url_for("dashboard_owner"))

    finally:
        if connection and connection.is_connected():
            connection.close()


# Tambahkan layanan dan harga.
@layanan_harga_bp.route("/tambah", methods=["POST"])
@owner_required
def tambah_layanan():
    nama = request.form.get("nama_layanan", "").strip()

    if not nama:
        flash("Nama layanan wajib diisi.", "error")
        return redirect(url_for("layanan_harga.daftar_layanan"))

    if len(nama) > 16:
        flash("Nama layanan maksimal 16 karakter.", "error")
        return redirect(url_for("layanan_harga.daftar_layanan"))

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        jenis_kendaraan = get_jenis_kendaraan(cursor)

        # Validasi harga sebelum disimpan.
        daftar_harga = {}

        for jenis in jenis_kendaraan:
            id_kendaraan = jenis["id_jenis_kendaraan"]
            nilai = request.form.get(f"harga_{id_kendaraan}", "").strip()

            if nilai == "":
                continue

            if not nilai.isdigit() or int(nilai) <= 0:
                raise ValueError(
                    f"Harga untuk {jenis['jenis_kendaraan']} harus berupa angka lebih dari 0."
                )

            daftar_harga[id_kendaraan] = int(nilai)

        cursor.execute("""
            INSERT INTO Jenis_Layanan (nama_layanan)
            VALUES (%s)
        """, (nama,))

        id_layanan = cursor.lastrowid

        for id_kendaraan, harga in daftar_harga.items():
            cursor.execute("""
                INSERT INTO Harga (
                    id_jenis_kendaraan,
                    id_jenis_layanan,
                    harga
                )
                VALUES (%s, %s, %s)
            """, (id_kendaraan, id_layanan, harga))

        connection.commit()
        cursor.close()

        flash("Layanan dan harga berhasil ditambahkan.", "success")

    except ValueError as e:
        if connection:
            connection.rollback()
        flash(str(e), "error")

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error tambah layanan:", e)

        if getattr(e, "errno", None) == 1062:
            flash("Nama layanan sudah terdaftar.", "error")
        else:
            flash("Gagal menambahkan layanan dan harga.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("layanan_harga.daftar_layanan"))


# Tampilkan form edit layanan dan harga.
@layanan_harga_bp.route("/edit/<int:id_layanan>")
@owner_required
def edit_layanan(id_layanan):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_jenis_layanan, nama_layanan, status
            FROM Jenis_Layanan
            WHERE id_jenis_layanan = %s
        """, (id_layanan,))
        layanan = cursor.fetchone()

        if not layanan:
            cursor.close()
            flash("Layanan tidak ditemukan.", "error")
            return redirect(url_for("layanan_harga.daftar_layanan"))

        jenis_kendaraan = get_jenis_kendaraan(cursor)

        cursor.execute("""
            SELECT id_jenis_kendaraan, harga
            FROM Harga
            WHERE id_jenis_layanan = %s
        """, (id_layanan,))
        harga_rows = cursor.fetchall()

        harga_edit = {
            row["id_jenis_kendaraan"]: row["harga"]
            for row in harga_rows
        }
        cursor.close()

        return render_template(
            "owner/layanan_harga.html",
            daftar_layanan=[],
            jenis_kendaraan=jenis_kendaraan,
            layanan_edit=layanan,
            harga_edit=harga_edit
        )

    except Exception as e:
        print("Error mengambil data edit layanan:", e)
        flash("Gagal mengambil data layanan.", "error")
        return redirect(url_for("layanan_harga.daftar_layanan"))

    finally:
        if connection and connection.is_connected():
            connection.close()


# Simpan perubahan nama layanan dan harga.
@layanan_harga_bp.route("/edit/<int:id_layanan>", methods=["POST"])
@owner_required
def simpan_edit_layanan(id_layanan):
    nama = request.form.get("nama_layanan", "").strip()

    if not nama:
        flash("Nama layanan wajib diisi.", "error")
        return redirect(url_for("layanan_harga.edit_layanan", id_layanan=id_layanan))

    if len(nama) > 16:
        flash("Nama layanan maksimal 16 karakter.", "error")
        return redirect(url_for("layanan_harga.edit_layanan", id_layanan=id_layanan))

    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_jenis_layanan
            FROM Jenis_Layanan
            WHERE id_jenis_layanan = %s
        """, (id_layanan,))

        if not cursor.fetchone():
            cursor.close()
            flash("Layanan tidak ditemukan.", "error")
            return redirect(url_for("layanan_harga.daftar_layanan"))

        jenis_kendaraan = get_jenis_kendaraan(cursor)

        # Validasi semua harga terlebih dahulu.
        daftar_harga = {}
        for jenis in jenis_kendaraan:
            id_kendaraan = jenis["id_jenis_kendaraan"]
            nilai = request.form.get(f"harga_{id_kendaraan}", "").strip()

            if nilai == "":
                daftar_harga[id_kendaraan] = None
                continue

            if not nilai.isdigit() or int(nilai) <= 0:
                raise ValueError(
                    f"Harga untuk {jenis['jenis_kendaraan']} harus berupa angka lebih dari 0."
                )

            daftar_harga[id_kendaraan] = int(nilai)

        cursor.execute("""
            UPDATE Jenis_Layanan
            SET nama_layanan = %s
            WHERE id_jenis_layanan = %s
        """, (nama, id_layanan))

        # Update atau hapus harga.
        for id_kendaraan, harga in daftar_harga.items():
            if harga is None:
                cursor.execute("""
                    DELETE FROM Harga
                    WHERE id_jenis_layanan = %s
                      AND id_jenis_kendaraan = %s
                """, (id_layanan, id_kendaraan))
            else:
                cursor.execute("""
                    INSERT INTO Harga (
                        id_jenis_kendaraan,
                        id_jenis_layanan,
                        harga
                    )
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE harga = VALUES(harga)
                """, (id_kendaraan, id_layanan, harga))

        connection.commit()
        cursor.close()

        flash("Layanan dan harga berhasil diperbarui.", "success")

    except ValueError as e:
        if connection:
            connection.rollback()
        flash(str(e), "error")
        return redirect(url_for("layanan_harga.edit_layanan", id_layanan=id_layanan))

    except Exception as e:
        if connection:
            connection.rollback()
        print("Error edit layanan:", e)

        if getattr(e, "errno", None) == 1062:
            flash("Nama layanan sudah digunakan.", "error")
        else:
            flash("Gagal memperbarui layanan dan harga.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("layanan_harga.daftar_layanan"))


# Nonaktifkan layanan.
@layanan_harga_bp.route("/nonaktifkan/<int:id_layanan>", methods=["POST"])
@owner_required
def nonaktifkan_layanan(id_layanan):
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Jenis_Layanan
            SET status = 'nonaktif'
            WHERE id_jenis_layanan = %s
              AND status = 'aktif'
        """, (id_layanan,))

        if cursor.rowcount == 0:
            flash("Layanan tidak ditemukan atau sudah nonaktif.", "error")
        else:
            connection.commit()
            flash("Layanan berhasil dinonaktifkan.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error nonaktifkan layanan:", e)
        flash("Gagal menonaktifkan layanan.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("layanan_harga.daftar_layanan"))


# Aktifkan kembali layanan.
@layanan_harga_bp.route("/aktifkan/<int:id_layanan>", methods=["POST"])
@owner_required
def aktifkan_layanan(id_layanan):
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Jenis_Layanan
            SET status = 'aktif'
            WHERE id_jenis_layanan = %s
              AND status = 'nonaktif'
        """, (id_layanan,))

        if cursor.rowcount == 0:
            flash("Layanan tidak ditemukan atau sudah aktif.", "error")
        else:
            connection.commit()
            flash("Layanan berhasil diaktifkan kembali.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()

        print("Error aktifkan layanan:", e)
        flash("Gagal mengaktifkan layanan.", "error")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("layanan_harga.daftar_layanan"))