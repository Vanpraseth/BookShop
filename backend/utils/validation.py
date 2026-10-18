from utils.errors import ValidationError


def positive_number(value, label):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a number.")
    if v <= 0:
        raise ValidationError(f"{label} must be greater than zero.")
    return round(v, 2)


def non_negative_int(value, label):
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a whole number.")
    if v < 0:
        raise ValidationError(f"{label} cannot be negative.")
    return v
