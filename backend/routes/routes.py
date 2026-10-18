from flask import Blueprint

from middleware.auth import login_required
from controllers import (
    auth_controller,
    book_controller,
    cart_controller,
    order_controller,
    admin_controller,
    shipment_controller,
    notification_controller,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
auth_bp.add_url_rule("/register", view_func=auth_controller.register, methods=["POST"])
auth_bp.add_url_rule("/login", view_func=auth_controller.login, methods=["POST"])

book_bp = Blueprint("books", __name__, url_prefix="/api/books")
book_bp.add_url_rule("", view_func=book_controller.list_books, methods=["GET"])
book_bp.add_url_rule("/<int:book_id>", view_func=book_controller.book_detail, methods=["GET"])

category_bp = Blueprint("categories", __name__, url_prefix="/api/categories")
category_bp.add_url_rule("", view_func=book_controller.list_categories, methods=["GET"])

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")
cart_bp.add_url_rule("", view_func=login_required()(cart_controller.view_cart), methods=["GET"])
cart_bp.add_url_rule("/items", view_func=login_required()(cart_controller.add_to_cart), methods=["POST"])
cart_bp.add_url_rule("/items/<int:book_id>", view_func=login_required()(cart_controller.update_cart), methods=["PATCH"])
cart_bp.add_url_rule("/items/<int:book_id>", view_func=login_required()(cart_controller.remove_from_cart), methods=["DELETE"])

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")
order_bp.add_url_rule("", view_func=login_required()(order_controller.create_order), methods=["POST"])
order_bp.add_url_rule("", view_func=login_required()(order_controller.order_history), methods=["GET"])
order_bp.add_url_rule("/<int:order_id>", view_func=login_required()(order_controller.order_detail), methods=["GET"])

shipment_bp = Blueprint("shipments", __name__, url_prefix="/api/shipments")
shipment_bp.add_url_rule("/track", view_func=login_required()(shipment_controller.track_shipments), methods=["GET"])

notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")
notification_bp.add_url_rule("", view_func=login_required()(notification_controller.list_notifications), methods=["GET"])
notification_bp.add_url_rule("/<int:notification_id>/read", view_func=login_required()(notification_controller.mark_notification_read), methods=["PATCH"])
notification_bp.add_url_rule("/read-all", view_func=login_required()(notification_controller.mark_all_notifications_read), methods=["PATCH"])

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
admin_bp.add_url_rule("/books", view_func=login_required(role="admin")(admin_controller.add_book), methods=["POST"])
admin_bp.add_url_rule("/books/<int:book_id>", view_func=login_required(role="admin")(admin_controller.edit_book), methods=["PUT"])
admin_bp.add_url_rule("/books/<int:book_id>", view_func=login_required(role="admin")(admin_controller.delete_book), methods=["DELETE"])
admin_bp.add_url_rule("/books/<int:book_id>/stock", view_func=login_required(role="admin")(admin_controller.set_stock), methods=["PATCH"])
admin_bp.add_url_rule("/shipments", view_func=login_required(role="admin")(admin_controller.list_shipments), methods=["GET"])
admin_bp.add_url_rule("/shipments/<int:order_id>", view_func=login_required(role="admin")(admin_controller.update_shipment), methods=["PATCH"])
admin_bp.add_url_rule("/reports/sales", view_func=login_required(role="admin")(admin_controller.sales_report), methods=["GET"])
admin_bp.add_url_rule("/reports/low-stock", view_func=login_required(role="admin")(admin_controller.low_stock_report), methods=["GET"])

ALL_BLUEPRINTS = [
    auth_bp, book_bp, category_bp, cart_bp, order_bp, shipment_bp,
    notification_bp, admin_bp
]
