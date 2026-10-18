import os


APPLICATION_NAME = os.environ.get("APP_NAME", "BookShop").strip() or "BookShop"
CURRENCY_CODE = os.environ.get("CURRENCY_CODE", "AUD").strip().upper() or "AUD"
DEFAULT_SHIPPING_ETA = (
    os.environ.get("DEFAULT_SHIPPING_ETA", "3-5 business days").strip()
    or "3-5 business days"
)
SHIPMENT_STATUSES = ("pending", "packed", "shipped", "delivered")
TRACKING_PREFIX = os.environ.get("TRACKING_PREFIX", "TRK").strip().upper() or "TRK"


def _bounded_int(name, default, minimum, maximum):
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


NOTIFICATION_POLL_SECONDS = _bounded_int(
    "NOTIFICATION_POLL_SECONDS", 30, 10, 300
)
TOKEN_MAX_AGE_SECONDS = _bounded_int("TOKEN_MAX_AGE", 86400, 300, 31_536_000)
MAX_CONTENT_LENGTH_BYTES = _bounded_int(
    "MAX_CONTENT_LENGTH_BYTES", 1_048_576, 1_024, 10_485_760
)
SERVER_PORT = _bounded_int("PORT", 5001, 1, 65_535)
SERVER_HOST = os.environ.get("HOST", "127.0.0.1").strip() or "127.0.0.1"


def public_config():
    return {
        "application_name": APPLICATION_NAME,
        "currency_code": CURRENCY_CODE,
        "shipment_statuses": list(SHIPMENT_STATUSES),
        "notification_poll_seconds": NOTIFICATION_POLL_SECONDS,
    }
