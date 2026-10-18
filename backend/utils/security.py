import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000


def hash_password(password, salt=None, iterations=_ITERATIONS):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"{_ALGORITHM}${iterations}${salt}${digest.hex()}"


def verify_password(password, stored):
    if not stored:
        return False

    if stored.startswith(f"{_ALGORITHM}$"):
        try:
            _, iterations, salt, _ = stored.split("$", 3)
            candidate = hash_password(password, salt, int(iterations))
        except (TypeError, ValueError):
            return False
        return hmac.compare_digest(candidate, stored)

    # Compatibility with databases created by earlier project versions.
    if stored.startswith("pbkdf2$"):
        try:
            _, salt, expected = stored.split("$", 2)
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()
        return hmac.compare_digest(digest, expected)

    return hmac.compare_digest(password, stored)


def password_needs_upgrade(stored):
    return not stored.startswith(f"{_ALGORITHM}${_ITERATIONS}$")
