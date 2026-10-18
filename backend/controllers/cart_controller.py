from flask import request, jsonify

from services.catalogue_service import CartService

cart_service = CartService()


def view_cart():
    return jsonify(cart_service.view(request.user["user_id"])), 200


def add_to_cart():
    data = request.get_json(silent=True) or {}
    result = cart_service.add(
        request.user["user_id"], data.get("book_id"), data.get("quantity", 1)
    )
    if result is None:
        return jsonify({"error": "Book not found."}), 404
    return jsonify(result), 200


def update_cart(book_id):
    data = request.get_json(silent=True) or {}
    result = cart_service.update(
        request.user["user_id"], book_id, data.get("quantity")
    )
    if result is None:
        return jsonify({"error": "Item not in cart."}), 404
    return jsonify(result), 200


def remove_from_cart(book_id):
    return jsonify(cart_service.remove(request.user["user_id"], book_id)), 200
