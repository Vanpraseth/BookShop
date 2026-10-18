from flask import request, jsonify

from services.report_service import ShipmentService

shipment_service = ShipmentService()


def track_shipments():
    return jsonify(shipment_service.track(request.user["user_id"])), 200
