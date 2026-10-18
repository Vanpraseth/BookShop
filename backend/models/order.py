"""Order domain classes."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OrderItem:
    book_id: int
    title: str
    quantity: int
    unit_price: float
    order_item_id: Optional[int] = None

    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    def to_dict(self) -> dict:
        return {
            "order_item_id": self.order_item_id,
            "book_id": self.book_id,
            "title": self.title,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal(),
        }


@dataclass
class Order:
    user_id: int
    delivery_address: str
    items: List[OrderItem] = field(default_factory=list)
    order_id: Optional[int] = None
    status: str = "processing"

    def calculate_total(self) -> float:
        return round(sum(item.subtotal() for item in self.items), 2)

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    def mark_paid(self) -> None:
        self.status = "paid"

    def mark_shipped(self) -> None:
        self.status = "shipped"

    def mark_delivered(self) -> None:
        self.status = "delivered"

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "delivery_address": self.delivery_address,
            "status": self.status,
            "total_price": self.calculate_total(),
            "items": [item.to_dict() for item in self.items],
        }


def order_item_from_row(row):
    if row is None:
        return None
    data = dict(row)
    return OrderItem(
        order_item_id=data.get("order_item_id"),
        book_id=data.get("book_id"),
        title=data.get("title"),
        quantity=data.get("quantity"),
        unit_price=data.get("unit_price"),
    )
