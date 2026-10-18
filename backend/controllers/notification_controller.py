from flask import jsonify, request

from services.notification_service import NotificationService


notification_service = NotificationService()


def list_notifications():
    unread_only = request.args.get("unread", "").strip().lower() in {
        "1", "true", "yes"
    }
    return jsonify(
        notification_service.list(request.user["user_id"], unread_only)
    ), 200


def mark_notification_read(notification_id):
    if not notification_service.mark_read(notification_id, request.user["user_id"]):
        return jsonify({"error": "Unread notification not found."}), 404
    return jsonify({"message": "Notification marked as read."}), 200


def mark_all_notifications_read():
    updated = notification_service.mark_all_read(request.user["user_id"])
    return jsonify({"updated": updated}), 200
