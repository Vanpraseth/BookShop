from flask import request, jsonify

from services.order_service import OrderService

order_service = OrderService()


def create_order():
    data = request.get_json(silent=True) or {}
    result = order_service.checkout(
        request.user["user_id"], data.get("delivery_address")
    )
    return jsonify(result), 201


def order_history():
    return jsonify(order_service.history(request.user["user_id"])), 200


def order_detail(order_id):
    order = order_service.detail(order_id, request.user["user_id"])
    if not order:
        return jsonify({"error": "Order not found."}), 404
    return jsonify(order), 200
