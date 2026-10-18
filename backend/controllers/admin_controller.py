from flask import request, jsonify

from services.catalogue_service import CatalogueService
from services.report_service import ReportService, ShipmentService

catalogue = CatalogueService()
report_service = ReportService()
shipment_service = ShipmentService()


def add_book():
    d = request.get_json(silent=True) or {}
    book = catalogue.add_book(
        d.get("title"), d.get("author"), d.get("description"),
        d.get("price"), d.get("category_id"), d.get("stock", 0)
    )
    return jsonify(book), 201


def edit_book(book_id):
    d = request.get_json(silent=True) or {}
    book = catalogue.edit_book(
        book_id, d.get("title"), d.get("author"), d.get("description"),
        d.get("price"), d.get("category_id")
    )
    if book is None:
        return jsonify({"error": "Book not found."}), 404
    return jsonify(book), 200


def delete_book(book_id):
    result = catalogue.remove_book(book_id)
    if result is None:
        return jsonify({"error": "Book not found."}), 404
    if result is False:
        return jsonify({"error": "This book is used by an existing cart or order and cannot be deleted."}), 409
    return jsonify({"message": "Deleted."}), 200


def set_stock(book_id):
    d = request.get_json(silent=True) or {}
    book = catalogue.set_stock(book_id, d.get("quantity"))
    if book is None:
        return jsonify({"error": "Book not found."}), 404
    return jsonify(book), 200


def update_shipment(order_id):
    d = request.get_json(silent=True) or {}
    shipment = shipment_service.update_status(order_id, d.get("status"))
    if shipment is None:
        return jsonify({"error": "Shipment not found."}), 404
    return jsonify(shipment), 200


def list_shipments():
    return jsonify(shipment_service.all()), 200


def sales_report():
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    return jsonify({
        "summary": report_service.summary(date_from, date_to),
        "best_sellers": report_service.best_sellers(),
    }), 200


def low_stock_report():
    return jsonify(report_service.low_stock()), 200
