import re

from repositories.report_repo import ReportRepository
from repositories.shipment_repo import ShipmentRepository
from utils.errors import ValidationError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ReportService:
    def __init__(self):
        self.reports = ReportRepository()

    def best_sellers(self):
        return self.reports.sales_report()

    def summary(self, date_from=None, date_to=None):
        for label, value in (("from", date_from), ("to", date_to)):
            if value and not _DATE_RE.match(value):
                raise ValidationError(
                    f"'{label}' must be YYYY-MM-DD."
                )
        return self.reports.sales_summary(date_from, date_to)

    def low_stock(self):
        return self.reports.low_stock()


class ShipmentService:
    def __init__(self):
        self.shipments = ShipmentRepository()

    def track(self, user_id):
        return self.shipments.track_for_user(user_id)

    def all(self):
        return self.shipments.list_all()

    def update_status(self, order_id, new_status):
        if not new_status:
            raise ValidationError("Status required.")
        valid = self.shipments.valid_statuses()
        if new_status not in valid:
            raise ValidationError(
                f"Status must be one of: {', '.join(valid)}."
            )
        result = self.shipments.update_status(order_id, new_status)
        return result.to_dict() if result else None
