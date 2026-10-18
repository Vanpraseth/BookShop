from flask import request, jsonify

from services.catalogue_service import CatalogueService

catalogue = CatalogueService()


def list_books():
    term = request.args.get("q")
    books = catalogue.search(term) if term else catalogue.browse()
    return jsonify(books), 200


def book_detail(book_id):
    book = catalogue.details(book_id)
    if not book:
        return jsonify({"error": "Book not found."}), 404
    return jsonify(book), 200


def list_categories():
    return jsonify(catalogue.categories()), 200
