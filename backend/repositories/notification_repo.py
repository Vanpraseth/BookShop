from db import get_connection, rows_to_list


class NotificationRepository:
    def list_for_user(self, user_id, unread_only=False, limit=50):
        conn = get_connection()
        try:
            where = " AND read_at IS NULL" if unread_only else ""
            rows = conn.execute(
                "SELECT notification_id, order_id, message, created_at, read_at"
                " FROM notifications WHERE user_id = ?" + where
                + " ORDER BY notification_id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()

    def unread_count(self, user_id):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM notifications"
                " WHERE user_id = ? AND read_at IS NULL",
                (user_id,),
            ).fetchone()
            return row["count"]
        finally:
            conn.close()

    def mark_read(self, notification_id, user_id):
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE notifications SET read_at = CURRENT_TIMESTAMP"
                " WHERE notification_id = ? AND user_id = ? AND read_at IS NULL",
                (notification_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def mark_all_read(self, user_id):
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE notifications SET read_at = CURRENT_TIMESTAMP"
                " WHERE user_id = ? AND read_at IS NULL",
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
