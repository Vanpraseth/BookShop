"""Cart domain classes."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CartItem:
    book_id: int
    title: str
    quantity: int
    price: float

    def subtotal(self) -> float:
        return round(self.quantity * self.price, 2)

    def to_dict(self) -> dict:
        return {
            "book_id": self.book_id,
            "title": self.title,
            "quantity": self.quantity,
            "price": self.price,
            "subtotal": self.subtotal(),
        }


@dataclass
class Cart:
    cart_id: Optional[int]
    user_id: int
    items: List[CartItem] = field(default_factory=list)

    def add_item(self, item: CartItem) -> None:
        for existing in self.items:
            if existing.book_id == item.book_id:
                existing.quantity += item.quantity
                return
        self.items.append(item)

    def update_quantity(self, book_id: int, quantity: int) -> None:
        if quantity <= 0:
            self.remove_item(book_id)
            return
        for item in self.items:
            if item.book_id == book_id:
                item.quantity = quantity
                return
        raise ValueError("Item not in cart.")

    def remove_item(self, book_id: int) -> None:
        self.items = [item for item in self.items if item.book_id != book_id]

    def total(self) -> float:
        return round(sum(item.subtotal() for item in self.items), 2)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def to_dict(self) -> dict:
        return {
            "cart_id": self.cart_id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "total": self.total(),
        }
