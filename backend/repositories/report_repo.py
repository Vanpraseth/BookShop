from db import get_connection, rows_to_list


class ReportRepository:
    def sales_report(self):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM sales_report_view"
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()

    def sales_summary(self, date_from=None, date_to=None):
        conn = get_connection()
        try:
            sql = (
                "SELECT COUNT(*) AS order_count,"
                "       COALESCE(SUM(total_price), 0) AS total_revenue"
                " FROM orders"
                " WHERE status IN ('paid','packed','shipped','delivered')"
            )
            params = []
            if date_from:
                sql += " AND date(created_at) >= date(?)"
                params.append(date_from)
            if date_to:
                sql += " AND date(created_at) <= date(?)"
                params.append(date_to)
            row = conn.execute(sql, params).fetchone()
            return dict(row)
        finally:
            conn.close()

    def low_stock(self):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT b.book_id, b.title, i.stock_quantity, i.low_stock_threshold"
                " FROM inventory i JOIN books b ON i.book_id = b.book_id"
                " WHERE i.stock_quantity <= i.low_stock_threshold"
                " ORDER BY i.stock_quantity ASC"
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()
