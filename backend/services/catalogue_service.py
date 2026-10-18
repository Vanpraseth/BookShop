import math

from repositories.book_repo import BookRepository
from repositories.cart_repo import CartRepository
from utils.errors import StockError, ValidationError


class CatalogueService:
    def __init__(self):
        self.books = BookRepository()

    def browse(self):
        return [b.to_dict() for b in self.books.list_all()]

    def categories(self):
        return self.books.list_categories()

    def search(self, term):
        if not term or not term.strip():
            return [b.to_dict() for b in self.books.list_all()]
        return [b.to_dict() for b in self.books.search(term.strip())]

    def details(self, book_id):
        book = self.books.find_by_id(book_id)
        return book.to_dict() if book else None

    def add_book(self, title, author, description, price, category_id, stock):
        title = _required_text(title, "Title", 160)
        author = _required_text(author, "Author", 160)
        description = _optional_text(description, "Description", 2000)
        price = _positive_number(price, "Price")
        category_id = _positive_int(category_id, "Category")
        if not self.books.category_exists(category_id):
            raise ValidationError("Category not found.")
        stock = _non_negative_int(stock, "Stock")
        book_id = self.books.create(title, author, description, price,
                                    category_id, stock)
        if book_id is None:
            raise ValidationError("Failed to add book.")
        book = self.books.find_by_id(book_id)
        return book.to_dict() if book else None

    def edit_book(self, book_id, title, author, description, price, category_id):
        if not self.books.find_by_id(book_id):
            return None
        title = _required_text(title, "Title", 160)
        author = _required_text(author, "Author", 160)
        description = _optional_text(description, "Description", 2000)
        price = _positive_number(price, "Price")
        category_id = _positive_int(category_id, "Category")
        if not self.books.category_exists(category_id):
            raise ValidationError("Category not found.")
        self.books.update(book_id, title, author, description, price, category_id)
        book = self.books.find_by_id(book_id)
        return book.to_dict() if book else None

    def remove_book(self, book_id):
        if not self.books.find_by_id(book_id):
            return None
        return self.books.delete(book_id)

    def set_stock(self, book_id, quantity):
        quantity = _non_negative_int(quantity, "Stock quantity")
        if not self.books.find_by_id(book_id):
            return None
        self.books.set_stock(book_id, quantity)
        book = self.books.find_by_id(book_id)
        return book.to_dict() if book else None


class CartService:
    def __init__(self):
        self.carts = CartRepository()
        self.books = BookRepository()

    def view(self, user_id):
        cart_id = self.carts.get_cart_id(user_id)
        items = self.carts.view(cart_id)
        total = round(sum(i["subtotal"] for i in items), 2)
        return {"items": items, "total": total}

    def add(self, user_id, book_id, quantity):
        quantity = _non_negative_int(quantity, "Quantity")
        if quantity < 1:
            raise ValidationError("Quantity min 1.")
        book = self.books.find_by_id(book_id)
        if not book:
            return None
        cart_id = self.carts.get_cart_id(user_id)
        requested_total = self.carts.item_quantity(cart_id, book_id) + quantity
        if not book.in_stock(requested_total):
            raise StockError(f"Only {book.stock_quantity} in stock.")
        self.carts.add_item(cart_id, book_id, quantity)
        return self.view(user_id)

    def update(self, user_id, book_id, quantity):
        quantity = _non_negative_int(quantity, "Quantity")
        cart_id = self.carts.get_cart_id(user_id)
        if quantity < 1:
            self.carts.remove_item(cart_id, book_id)
            return self.view(user_id)
        book = self.books.find_by_id(book_id)
        if book and not book.in_stock(quantity):
            raise StockError(f"Only {book.stock_quantity} in stock.")
        if not self.carts.update_quantity(cart_id, book_id, quantity):
            return None
        return self.view(user_id)

    def remove(self, user_id, book_id):
        cart_id = self.carts.get_cart_id(user_id)
        self.carts.remove_item(cart_id, book_id)
        return self.view(user_id)


def _positive_number(value, label):
    if isinstance(value, bool):
        raise ValidationError(f"{label} must be a number.")
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a number.")
    if not math.isfinite(v) or v <= 0:
        raise ValidationError(f"{label} must be > 0.")
    return round(v, 2)


def _non_negative_int(value, label):
    if isinstance(value, bool):
        raise ValidationError(f"{label} must be a whole number.")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a whole number.")
    if not number.is_integer():
        raise ValidationError(f"{label} must be a whole number.")
    v = int(number)
    if v < 0:
        raise ValidationError(f"{label} cannot be negative.")
    return v


def _positive_int(value, label):
    value = _non_negative_int(value, label)
    if value < 1:
        raise ValidationError(f"{label} must be a positive whole number.")
    return value


def _required_text(value, label, maximum):
    value = value.strip() if isinstance(value, str) else ""
    if not value:
        raise ValidationError(f"{label} required.")
    if len(value) > maximum:
        raise ValidationError(f"{label} must be {maximum} characters or fewer.")
    return value


def _optional_text(value, label, maximum):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be text.")
    value = value.strip()
    if len(value) > maximum:
        raise ValidationError(f"{label} must be {maximum} characters or fewer.")
    return value
