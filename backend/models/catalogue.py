"""Catalogue domain class."""

from dataclasses import dataclass, field
from typing import List, Optional

from models.book import Book


@dataclass
class Catalogue:
    books: List[Book] = field(default_factory=list)

    def add_book(self, book: Book) -> None:
        self.books.append(book)

    def find_book(self, book_id: int) -> Optional[Book]:
        return next((book for book in self.books if book.book_id == book_id), None)

    def search(self, term: str) -> List[Book]:
        search_term = (term or "").lower()
        return [
            book for book in self.books
            if search_term in book.title.lower()
            or search_term in (book.author or "").lower()
            or search_term in (book.category_name or "").lower()
        ]

    def to_dict(self) -> dict:
        return {"books": [book.to_dict() for book in self.books]}
