from repositories.notification_repo import NotificationRepository


class NotificationService:
    def __init__(self):
        self.notifications = NotificationRepository()

    def list(self, user_id, unread_only=False):
        return {
            "items": self.notifications.list_for_user(user_id, unread_only),
            "unread_count": self.notifications.unread_count(user_id),
        }

    def mark_read(self, notification_id, user_id):
        return self.notifications.mark_read(notification_id, user_id)

    def mark_all_read(self, user_id):
        return self.notifications.mark_all_read(user_id)
