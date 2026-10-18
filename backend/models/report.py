"""Sales report domain class."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SalesReport:
    total_orders: int = 0
    total_sales: float = 0.0
    best_sellers: List[dict] = field(default_factory=list)
    low_stock_items: List[dict] = field(default_factory=list)

    def add_best_seller(self, book_id: int, title: str, quantity_sold: int, total_sales: float) -> None:
        self.best_sellers.append({
            "book_id": book_id,
            "title": title,
            "quantity_sold": quantity_sold,
            "total_sales": round(total_sales, 2),
        })

    def add_low_stock_item(self, book_id: int, title: str, stock_quantity: int) -> None:
        self.low_stock_items.append({
            "book_id": book_id,
            "title": title,
            "stock_quantity": stock_quantity,
        })

    def to_dict(self) -> dict:
        return {
            "total_orders": self.total_orders,
            "total_sales": round(self.total_sales, 2),
            "best_sellers": self.best_sellers,
            "low_stock_items": self.low_stock_items,
        }
