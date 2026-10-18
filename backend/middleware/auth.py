from functools import wraps

from flask import request, jsonify

from services.auth_service import AuthService

auth_service = AuthService()


def _token_from_request():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = auth_service.user_for_token(_token_from_request())
            if not user:
                return jsonify({"error": "Login required."}), 401
            if role and user["role"] != role:
                return jsonify({"error": "Access denied."}), 403
            request.user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator
