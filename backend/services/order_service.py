from repositories.cart_repo import CartRepository
from repositories.order_repo import OrderRepository
from repositories.book_repo import BookRepository
from utils.errors import StockError, ValidationError


class OrderService:
    def __init__(self):
        self.carts = CartRepository()
        self.orders = OrderRepository()
        self.books = BookRepository()

    def checkout(self, user_id, delivery_address):
        delivery_address = (
            delivery_address.strip() if isinstance(delivery_address, str) else ""
        )
        if not delivery_address:
            raise ValidationError("Address required.")
        if len(delivery_address) > 300:
            raise ValidationError("Address must be 300 characters or fewer.")

        cart_id = self.carts.get_cart_id(user_id)
        cart_items = self.carts.view(cart_id)
        if not cart_items:
            raise ValidationError("Cart is empty.")

        items = []
        for ci in cart_items:
            available = self.books.get_stock(ci["book_id"])
            if available < ci["quantity"]:
                raise StockError(
                    f"'{ci['title']}' only has {available} in stock."
                )
            items.append({
                "book_id": ci["book_id"],
                "title": ci["title"],
                "quantity": ci["quantity"],
                "price": ci["price"],
            })

        order_id, total = self.orders.create_order(
            user_id, cart_id, delivery_address, items
        )
        return {
            "order_id": order_id,
            "total_price": total,
            "status": "paid",
            "message": "Order placed. Payment processed, invoice and shipment created.",
        }

    def history(self, user_id):
        return self.orders.history(user_id)

    def detail(self, order_id, user_id):
        return self.orders.get_with_items(order_id, user_id)
