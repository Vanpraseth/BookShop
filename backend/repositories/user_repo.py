import sqlite3

from db import get_connection, row_to_dict


class UserRepository:
    def create(self, full_name, email, password_hash, role="customer"):
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO users (full_name, email, password, role) VALUES (?, ?, ?, ?)",
                (full_name, email, password_hash, role),
            )
            user_id = cur.lastrowid
            conn.execute("INSERT INTO carts (user_id) VALUES (?)", (user_id,))
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            conn.rollback()
            return None
        finally:
            conn.close()

    def find_by_email(self, email):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT user_id, full_name, email, password, role"
                " FROM users WHERE lower(email) = lower(?)",
                (email,),
            ).fetchone()
            return row_to_dict(row)
        finally:
            conn.close()

    def find_by_id(self, user_id):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT user_id, full_name, email, role FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return row_to_dict(row)
        finally:
            conn.close()

    def update_password(self, user_id, new_hash):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE users SET password = ? WHERE user_id = ?", (new_hash, user_id)
            )
            conn.commit()
        finally:
            conn.close()
