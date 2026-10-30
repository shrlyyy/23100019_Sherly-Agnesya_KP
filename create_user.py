from werkzeug.security import generate_password_hash
from database import get_db_connection

connection = get_db_connection()
cursor = connection.cursor()

username = input("Masukkan username: ")
password = input("Masukkan password: ")
role = input("Masukkan role (owner/admin): ").strip().lower()

if role not in ["owner", "admin"]:
    print("Role tidak valid.")

else:
    password_hash = generate_password_hash(password)

    query = """
        INSERT INTO User (username, password, role)
        VALUES (%s, %s, %s)
    """

    try:
        cursor.execute(query, (username, password_hash, role))
        connection.commit()
        print("Akun berhasil dibuat!")

    except Exception as e:
        connection.rollback()
        print("Gagal membuat akun:", e)

cursor.close()
connection.close()