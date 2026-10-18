from flask import request, jsonify

from services.auth_service import AuthService

auth_service = AuthService()


def register():
    data = request.get_json(silent=True) or {}
    user = auth_service.register(
        data.get("full_name"), data.get("email"), data.get("password")
    )
    return jsonify(user), 201


def login():
    data = request.get_json(silent=True) or {}
    result = auth_service.login(data.get("email"), data.get("password"))
    if not result:
        return jsonify({"error": "Invalid credentials."}), 401
    return jsonify(result), 200
