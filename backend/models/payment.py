from abc import ABC, abstractmethod

from config import CURRENCY_CODE, SHIPMENT_STATUSES


class PaymentMethod(ABC):
    @abstractmethod
    def pay(self, amount):
        ...


class Card(PaymentMethod):
    def __init__(self, card_number=None):
        self.card_number = card_number

    def pay(self, amount):
        return {
            "method": "card",
            "status": "processed",
            "message": f"Card charged {CURRENCY_CODE} {amount:.2f}.",
        }


class OnlinePayment(PaymentMethod):
    def __init__(self, provider="online"):
        self.provider = provider

    def pay(self, amount):
        return {
            "method": "online",
            "status": "processed",
            "message": f"Paid {CURRENCY_CODE} {amount:.2f} via {self.provider}.",
        }


class Payment:
    def __init__(self, order_id, amount, method: PaymentMethod):
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.result = None

    def process(self):
        self.result = self.method.pay(self.amount)
        return self.result

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "amount": self.amount,
            "result": self.result,
        }


class Invoice:
    def __init__(self, order_id, receipt_message=None, invoice_id=None):
        self.invoice_id = invoice_id
        self.order_id = order_id
        self.receipt_message = receipt_message

    def to_dict(self):
        return {
            "invoice_id": self.invoice_id,
            "order_id": self.order_id,
            "receipt_message": self.receipt_message,
        }


class Shipment:
    def __init__(self, order_id, tracking_number=None,
                 shipment_status=None, eta=None, shipment_id=None):
        self.shipment_id = shipment_id
        self.order_id = order_id
        self.tracking_number = tracking_number
        self.shipment_status = shipment_status or SHIPMENT_STATUSES[0]
        self.eta = eta

    def to_dict(self):
        return {
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "tracking_number": self.tracking_number,
            "shipment_status": self.shipment_status,
            "eta": self.eta,
        }


def shipment_from_row(row):
    if row is None:
        return None
    return Shipment(
        row["order_id"], row.get("tracking_number"),
        row.get("shipment_status") or SHIPMENT_STATUSES[0], row.get("eta"),
        row.get("shipment_id"),
    )
