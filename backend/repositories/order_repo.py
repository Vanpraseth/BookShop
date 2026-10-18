import secrets

from config import DEFAULT_SHIPPING_ETA, SHIPMENT_STATUSES, TRACKING_PREFIX
from db import get_connection, rows_to_list
from models.payment import Payment, Card, Invoice
from utils.errors import StockError


class OrderRepository:
    def create_order(self, user_id, cart_id, delivery_address, items):
        total = round(sum(i["price"] * i["quantity"] for i in items), 2)
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                "INSERT INTO orders (user_id, delivery_address, total_price, status)"
                " VALUES (?, ?, ?, 'processing')",
                (user_id, delivery_address, total),
            )
            order_id = cur.lastrowid

            for it in items:
                subtotal = round(it["price"] * it["quantity"], 2)
                conn.execute(
                    "INSERT INTO order_items (order_id, book_id, quantity, unit_price, subtotal)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (order_id, it["book_id"], it["quantity"], it["price"], subtotal),
                )
                cursor = conn.execute(
                    "UPDATE inventory SET stock_quantity = stock_quantity - ?"
                    " WHERE book_id = ? AND stock_quantity >= ?",
                    (it["quantity"], it["book_id"], it["quantity"]),
                )
                if cursor.rowcount != 1:
                    raise StockError(
                        f"'{it['title']}' no longer has enough stock."
                    )

            payment = Payment(order_id, total, Card())
            result = payment.process()
            conn.execute(
                "INSERT INTO payments (order_id, amount, payment_method, payment_status)"
                " VALUES (?, ?, ?, ?)",
                (order_id, total, result["method"], result["status"]),
            )

            invoice = Invoice(order_id, result["message"])
            conn.execute(
                "INSERT INTO invoices (order_id, receipt_message) VALUES (?, ?)",
                (order_id, invoice.receipt_message),
            )

            tracking = f"{TRACKING_PREFIX}-{secrets.token_hex(5).upper()}"
            conn.execute(
                "INSERT INTO shipments (order_id, tracking_number, shipment_status, eta)"
                " VALUES (?, ?, ?, ?)",
                (order_id, tracking, SHIPMENT_STATUSES[0], DEFAULT_SHIPPING_ETA),
            )
            conn.execute(
                "UPDATE orders SET status = 'paid' WHERE order_id = ?", (order_id,)
            )
            conn.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))

            conn.commit()
            return order_id, total
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def history(self, user_id):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT order_id, delivery_address, total_price, status, created_at"
                " FROM orders WHERE user_id = ? ORDER BY order_id DESC",
                (user_id,),
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()

    def get_with_items(self, order_id, user_id):
        conn = get_connection()
        try:
            order = conn.execute(
                "SELECT o.order_id, o.delivery_address, o.total_price, o.status,"
                "       s.tracking_number, s.shipment_status, s.eta"
                " FROM orders o LEFT JOIN shipments s ON o.order_id = s.order_id"
                " WHERE o.order_id = ? AND o.user_id = ?",
                (order_id, user_id),
            ).fetchone()
            if not order:
                return None
            items = conn.execute(
                "SELECT oi.book_id, b.title, oi.quantity, oi.unit_price, oi.subtotal"
                " FROM order_items oi JOIN books b ON oi.book_id = b.book_id"
                " WHERE oi.order_id = ?",
                (order_id,),
            ).fetchall()
            result = dict(order)
            result["items"] = rows_to_list(items)
            return result
        finally:
            conn.close()
