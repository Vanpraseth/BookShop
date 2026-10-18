import sqlite3

from db import get_connection, row_to_dict
from models.book import book_from_row

_BOOK_SELECT = """
SELECT b.book_id, b.title, b.author, b.description, b.price, b.category_id,
       c.category_name, i.stock_quantity
FROM books b
LEFT JOIN categories c ON b.category_id = c.category_id
LEFT JOIN inventory  i ON b.book_id     = i.book_id
"""


class BookRepository:
    def list_categories(self):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT category_id, category_name FROM categories ORDER BY category_name"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def list_all(self):
        conn = get_connection()
        try:
            rows = conn.execute(_BOOK_SELECT + " ORDER BY b.title").fetchall()
            return [book_from_row(dict(r)) for r in rows]
        finally:
            conn.close()

    def search(self, term):
        like = f"%{term}%"
        conn = get_connection()
        try:
            rows = conn.execute(
                _BOOK_SELECT
                + " WHERE b.title LIKE ? OR b.author LIKE ? OR c.category_name LIKE ?"
                + " ORDER BY b.title",
                (like, like, like),
            ).fetchall()
            return [book_from_row(dict(r)) for r in rows]
        finally:
            conn.close()

    def find_by_id(self, book_id):
        conn = get_connection()
        try:
            row = conn.execute(
                _BOOK_SELECT + " WHERE b.book_id = ?", (book_id,)
            ).fetchone()
            return book_from_row(row_to_dict(row))
        finally:
            conn.close()

    def create(self, title, author, description, price, category_id, stock):
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO books (title, author, description, price, category_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (title, author, description, price, category_id),
            )
            book_id = cur.lastrowid
            conn.execute(
                "INSERT INTO inventory (book_id, stock_quantity) VALUES (?, ?)",
                (book_id, stock),
            )
            conn.commit()
            return book_id
        except sqlite3.IntegrityError:
            conn.rollback()
            return None
        finally:
            conn.close()

    def update(self, book_id, title, author, description, price, category_id):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE books SET title=?, author=?, description=?, price=?, category_id=?"
                " WHERE book_id=?",
                (title, author, description, price, category_id, book_id),
            )
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def delete(self, book_id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM inventory WHERE book_id = ?", (book_id,))
            conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        finally:
            conn.close()

    def set_stock(self, book_id, quantity):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE inventory SET stock_quantity = ? WHERE book_id = ?",
                (quantity, book_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_stock(self, book_id):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT stock_quantity FROM inventory WHERE book_id = ?", (book_id,)
            ).fetchone()
            return row["stock_quantity"] if row else 0
        finally:
            conn.close()

    def category_exists(self, category_id):
        conn = get_connection()
        try:
            return conn.execute(
                "SELECT 1 FROM categories WHERE category_id = ?", (category_id,)
            ).fetchone() is not None
        finally:
            conn.close()

    def decrement_stock(self, conn, book_id, quantity):
        conn.execute(
            "UPDATE inventory SET stock_quantity = stock_quantity - ? WHERE book_id = ?",
            (quantity, book_id),
        )
