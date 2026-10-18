class Category:
    def __init__(self, category_id=None, category_name=None):
        self.category_id = category_id
        self.category_name = category_name

    def to_dict(self):
        return {"category_id": self.category_id,
                "category_name": self.category_name}


class Book:
    def __init__(self, book_id, title, author, description, price,
                 category_id=None, category_name=None, stock_quantity=0):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.description = description
        self.price = price
        self.category_id = category_id
        self.category_name = category_name
        self.stock_quantity = stock_quantity

    def in_stock(self, quantity=1):
        return self.stock_quantity >= quantity

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "price": self.price,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "stock_quantity": self.stock_quantity,
        }


class Inventory:
    def __init__(self, book_id, stock_quantity=0, low_stock_threshold=3):
        self.book_id = book_id
        self.stock_quantity = stock_quantity
        self.low_stock_threshold = low_stock_threshold

    def is_low(self):
        return self.stock_quantity <= self.low_stock_threshold

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "stock_quantity": self.stock_quantity,
            "low_stock_threshold": self.low_stock_threshold,
        }


def book_from_row(row):
    if row is None:
        return None
    return Book(
        row["book_id"], row["title"], row.get("author"),
        row.get("description"), row["price"],
        row.get("category_id"), row.get("category_name"),
        row.get("stock_quantity", 0),
    )
