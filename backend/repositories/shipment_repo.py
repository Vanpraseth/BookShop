from config import SHIPMENT_STATUSES
from db import get_connection, row_to_dict, rows_to_list
from models.payment import shipment_from_row


class ShipmentRepository:
    def list_all(self):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT s.shipment_id, s.order_id, s.tracking_number,"
                "       s.shipment_status, s.eta, o.total_price, o.created_at,"
                "       u.full_name AS customer_name"
                " FROM shipments s"
                " JOIN orders o ON s.order_id = o.order_id"
                " JOIN users u ON o.user_id = u.user_id"
                " ORDER BY s.order_id DESC"
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()

    def track_for_user(self, user_id):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT o.order_id, o.status, s.tracking_number,"
                "       s.shipment_status, s.eta"
                " FROM orders o JOIN shipments s ON o.order_id = s.order_id"
                " WHERE o.user_id = ?"
                " ORDER BY o.order_id DESC",
                (user_id,),
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()

    def find_by_order(self, order_id):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT shipment_id, order_id, tracking_number, shipment_status, eta"
                " FROM shipments WHERE order_id = ?",
                (order_id,),
            ).fetchone()
            return shipment_from_row(row_to_dict(row))
        finally:
            conn.close()

    def update_status(self, order_id, new_status):
        conn = get_connection()
        try:
            existing = conn.execute(
                "SELECT s.shipment_id, s.shipment_status, o.user_id"
                " FROM shipments s JOIN orders o ON s.order_id = o.order_id"
                " WHERE s.order_id = ?",
                (order_id,),
            ).fetchone()
            if not existing:
                return None
            if existing["shipment_status"] == new_status:
                return shipment_from_row(row_to_dict(conn.execute(
                    "SELECT shipment_id, order_id, tracking_number,"
                    " shipment_status, eta FROM shipments WHERE order_id = ?",
                    (order_id,),
                ).fetchone()))
            conn.execute(
                "UPDATE shipments SET shipment_status = ? WHERE order_id = ?",
                (new_status, order_id),
            )
            if new_status in ("shipped", "delivered"):
                conn.execute(
                    "UPDATE orders SET status = ? WHERE order_id = ?",
                    (new_status, order_id),
                )
            conn.execute(
                "INSERT INTO notifications (user_id, order_id, message)"
                " VALUES (?, ?, ?)",
                (
                    existing["user_id"],
                    order_id,
                    f"Order #{order_id} shipment status changed to {new_status}.",
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT shipment_id, order_id, tracking_number, shipment_status, eta"
                " FROM shipments WHERE order_id = ?",
                (order_id,),
            ).fetchone()
            return shipment_from_row(row_to_dict(row))
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def valid_statuses():
        return SHIPMENT_STATUSES
