"""User-related domain classes for the BookShop application.

These classes represent the account objects identified in the object design.
They are intentionally small domain/model classes. Validation and database
access stay in the service and repository layers.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Base account class shared by all system users."""

    user_id: Optional[int]
    full_name: str
    email: str
    role: str = "customer"

    def can_login(self) -> bool:
        """Return True when the account has enough data to authenticate."""
        return bool(self.email and self.full_name)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
        }


@dataclass
class Customer(User):
    """Registered customer who can browse books, manage a cart and order."""

    role: str = "customer"

    def can_place_order(self) -> bool:
        return self.role == "customer" and self.can_login()


@dataclass
class Admin(User):
    """Administrator responsible for catalogue, stock and reports."""

    role: str = "admin"

    def can_manage_catalogue(self) -> bool:
        return self.role == "admin"


@dataclass
class Employee(User):
    """Employee/staff user for packaging and delivery preparation tasks."""

    role: str = "employee"

    def can_process_shipments(self) -> bool:
        return self.role in ("employee", "admin")


def user_from_row(row):
    """Build the correct User subclass from a sqlite row/dict."""
    if row is None:
        return None
    data = dict(row)
    role = data.get("role", "customer")
    cls = {"admin": Admin, "employee": Employee}.get(role, Customer)
    return cls(
        user_id=data.get("user_id"),
        full_name=data.get("full_name"),
        email=data.get("email"),
        role=role,
    )
