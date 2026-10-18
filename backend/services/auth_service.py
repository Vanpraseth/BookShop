import re

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from repositories.user_repo import UserRepository
from utils.errors import ValidationError
from utils.security import hash_password, password_needs_upgrade, verify_password

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _token_serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"], salt="bookshop-auth"
    )


class AuthService:
    def __init__(self):
        self.users = UserRepository()

    def register(self, full_name, email, password):
        full_name = full_name.strip() if isinstance(full_name, str) else ""
        if not full_name:
            raise ValidationError("Name required.")
        if len(full_name) > 120:
            raise ValidationError("Name must be 120 characters or fewer.")
        email = email.strip().lower() if email else ""
        if not _EMAIL_RE.match(email):
            raise ValidationError("Invalid email.")
        if len(email) > 254:
            raise ValidationError("Email must be 254 characters or fewer.")
        if not isinstance(password, str) or len(password) < 8:
            raise ValidationError("Password must contain at least 8 characters.")
        if len(password) > 128:
            raise ValidationError("Password must be 128 characters or fewer.")
        if self.users.find_by_email(email):
            raise ValidationError("Email already in use.")

        user_id = self.users.create(full_name, email, hash_password(password))
        if user_id is None:
            raise ValidationError("Registration failed.")
        return {"user_id": user_id, "full_name": full_name,
                "email": email, "role": "customer"}

    def login(self, email, password):
        if not email or not password:
            raise ValidationError("Email and password required.")
        email = email.strip().lower()
        row = self.users.find_by_email(email)
        if not row or not verify_password(password, row["password"]):
            return None

        if password_needs_upgrade(row["password"]):
            self.users.update_password(row["user_id"], hash_password(password))

        user = {"user_id": row["user_id"], "full_name": row["full_name"],
                "email": row["email"], "role": row["role"]}
        token = _token_serializer().dumps({"user_id": user["user_id"]})
        return {"token": token, "user": user}

    @staticmethod
    def user_for_token(token):
        if not token:
            return None
        try:
            data = _token_serializer().loads(
                token, max_age=current_app.config["TOKEN_MAX_AGE"]
            )
            user_id = int(data["user_id"])
        except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
            return None
        return UserRepository().find_by_id(user_id)
