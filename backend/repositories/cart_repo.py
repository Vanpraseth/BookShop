from db import get_connection, row_to_dict, rows_to_list


class CartRepository:
    def get_cart_id(self, user_id):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT cart_id FROM carts WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row:
                return row["cart_id"]
            cur = conn.execute("INSERT INTO carts (user_id) VALUES (?)", (user_id,))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def view(self, cart_id):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT ci.cart_item_id, b.book_id, b.title, ci.quantity, b.price,"
                "       ci.quantity * b.price AS subtotal"
                " FROM cart_items ci JOIN books b ON ci.book_id = b.book_id"
                " WHERE ci.cart_id = ?",
                (cart_id,),
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()

    def add_item(self, cart_id, book_id, quantity):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO cart_items (cart_id, book_id, quantity) VALUES (?, ?, ?)"
                " ON CONFLICT(cart_id, book_id)"
                " DO UPDATE SET quantity = quantity + excluded.quantity",
                (cart_id, book_id, quantity),
            )
            conn.commit()
        finally:
            conn.close()

    def item_quantity(self, cart_id, book_id):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT quantity FROM cart_items WHERE cart_id = ? AND book_id = ?",
                (cart_id, book_id),
            ).fetchone()
            return row["quantity"] if row else 0
        finally:
            conn.close()

    def update_quantity(self, cart_id, book_id, quantity):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND book_id = ?",
                (quantity, cart_id, book_id),
            )
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def remove_item(self, cart_id, book_id):
        conn = get_connection()
        try:
            conn.execute(
                "DELETE FROM cart_items WHERE cart_id = ? AND book_id = ?",
                (cart_id, book_id),
            )
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()

    def clear(self, conn, cart_id):
        conn.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
