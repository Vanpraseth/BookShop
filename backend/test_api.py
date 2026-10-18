"""
Runs all API scenarios using Flask's built-in test client.
No server needed — just run this file directly.
"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEST_DIRECTORY = tempfile.TemporaryDirectory(prefix="bookshop-tests-")
_TEST_DATABASE = Path(_TEST_DIRECTORY.name) / "bookshop-test.db"

os.environ["APP_ENV"] = "testing"
os.environ["BOOKSHOP_DB"] = str(_TEST_DATABASE)
os.environ["SECRET_KEY"] = "test-only-secret-key"
os.environ["ADMIN_NAME"] = "Integration Admin"
os.environ["ADMIN_EMAIL"] = "integration-admin@example.test"
os.environ["ADMIN_PASSWORD"] = "integration-admin-password"

with sqlite3.connect(_TEST_DATABASE) as connection:
    connection.executescript((_PROJECT_ROOT / "database" / "schema.sql").read_text())
    connection.executescript((_PROJECT_ROOT / "database" / "catalogue_data.sql").read_text())

import server as application

client = application.app.test_client()


def show(label, resp):
    try:
        body = resp.get_json()
    except Exception:
        body = resp.data.decode()
    print(f"\n[{resp.status_code}] {label}")
    print(json.dumps(body, indent=2)[:600])


print("=" * 55)
print("BOOKSHOP API - TEST RUN")
print("=" * 55)

# --- Public catalogue ---
config_response = client.get("/api/config")
show("Public application configuration", config_response)
assert config_response.status_code == 200
assert config_response.get_json()["application_name"] == "BookShop"
categories_response = client.get("/api/categories")
show("Browse categories", categories_response)
assert categories_response.status_code == 200
assert len(categories_response.get_json()) == 4
show("Browse all books (public, no login)", client.get("/api/books"))
show("Search q=security", client.get("/api/books?q=security"))
show("Book detail id=1", client.get("/api/books/1"))
show("Book detail id=999 (not found)", client.get("/api/books/999"))

# --- Registration validation ---
registration = client.post("/api/auth/register", json={
    "full_name": "Test User", "email": "test@example.com", "password": "secret123"})
show("Register VALID", registration)
assert registration.status_code == 201
with sqlite3.connect(_TEST_DATABASE) as connection:
    saved_user = connection.execute(
        "SELECT full_name, email, password FROM users WHERE email = ?",
        ("test@example.com",),
    ).fetchone()
assert saved_user[:2] == ("Test User", "test@example.com")
assert saved_user[2] != "secret123" and saved_user[2].startswith("pbkdf2_sha256$")
show("Register invalid email (expect 400)", client.post("/api/auth/register", json={
    "full_name": "Bad", "email": "notanemail", "password": "secret123"}))
show("Register short password (expect 400)", client.post("/api/auth/register", json={
    "full_name": "Bad", "email": "x@y.com", "password": "12"}))
show("Register blank name (expect 400)", client.post("/api/auth/register", json={
    "full_name": "", "email": "z@y.com", "password": "secret123"}))

# --- Login ---
show("Login wrong password (expect 401)", client.post("/api/auth/login", json={
    "email": "test@example.com", "password": "wrong"}))
login = client.post("/api/auth/login", json={
    "email": "test@example.com", "password": "secret123"})
show("Login VALID", login)
token = login.get_json()["token"]
H = {"Authorization": f"Bearer {token}"}

# --- Cart (auth) ---
show("View cart without token (expect 401)", client.get("/api/cart"))
show("Add book 1 x2 to cart", client.post("/api/cart/items",
     json={"book_id": 1, "quantity": 2}, headers=H))
show("Add book 4 x5 - only 2 in stock (expect 409)", client.post(
     "/api/cart/items", json={"book_id": 4, "quantity": 5}, headers=H))
show("Add book 4 x1 (ok)", client.post("/api/cart/items",
     json={"book_id": 4, "quantity": 1}, headers=H))
cumulative_stock = client.post(
    "/api/cart/items", json={"book_id": 4, "quantity": 2}, headers=H
)
show("Add book 4 x2 again - cumulative quantity exceeds stock (expect 409)", cumulative_stock)
assert cumulative_stock.status_code == 409
show("Update book 1 -> qty 3 (change of mind)", client.patch(
     "/api/cart/items/1", json={"quantity": 3}, headers=H))
show("Update book 4 -> qty 0 (removal)", client.patch(
     "/api/cart/items/4", json={"quantity": 0}, headers=H))
show("View cart", client.get("/api/cart", headers=H))

# --- Checkout ---
show("Checkout no address (expect 400)", client.post("/api/orders",
     json={}, headers=H))
checkout = client.post("/api/orders",
     json={"delivery_address": "100 Example Street, Melbourne VIC 3000"}, headers=H)
show("Checkout VALID", checkout)
assert checkout.status_code == 201
order_id = checkout.get_json()["order_id"]
with sqlite3.connect(_TEST_DATABASE) as connection:
    saved_order = connection.execute(
        "SELECT delivery_address, status FROM orders WHERE order_id = ?", (order_id,)
    ).fetchone()
    saved_payment = connection.execute(
        "SELECT payment_status FROM payments WHERE order_id = ?", (order_id,)
    ).fetchone()
    saved_invoice = connection.execute(
        "SELECT receipt_message FROM invoices WHERE order_id = ?", (order_id,)
    ).fetchone()
    saved_shipment = connection.execute(
        "SELECT shipment_status FROM shipments WHERE order_id = ?", (order_id,)
    ).fetchone()
    remaining_stock = connection.execute(
        "SELECT stock_quantity FROM inventory WHERE book_id = 1"
    ).fetchone()[0]
    remaining_cart_items = connection.execute("SELECT COUNT(*) FROM cart_items").fetchone()[0]
assert saved_order == ("100 Example Street, Melbourne VIC 3000", "paid")
assert saved_payment == ("processed",)
assert saved_invoice and saved_invoice[0]
assert saved_shipment == ("pending",)
assert remaining_stock == 7
assert remaining_cart_items == 0
show("Order history", client.get("/api/orders", headers=H))
show("Order detail", client.get(f"/api/orders/{order_id}", headers=H))

# --- Admin ---
admin = client.post("/api/auth/login", json={
    "email": "integration-admin@example.test",
    "password": "integration-admin-password",
})
AH = {"Authorization": f"Bearer {admin.get_json()['token']}"}
show("Customer hits admin route (expect 403)", client.post(
     "/api/admin/books", json={"title": "X", "price": 10}, headers=H))
show("Admin add book", client.post("/api/admin/books", json={
     "title": "Clean Code", "author": "R. Martin", "description": "Craftsmanship",
     "price": 55.00, "category_id": 1, "stock": 7}, headers=AH))
show("Admin add book invalid price (expect 400)", client.post(
     "/api/admin/books", json={"title": "Bad", "author": "Test Author",
     "description": "Invalid price test", "category_id": 1, "stock": 1,
     "price": -5}, headers=AH))
show("Admin set stock book 1 -> 20", client.patch(
     "/api/admin/books/1/stock", json={"quantity": 20}, headers=AH))

# --- Shipment tracking ---
show("Customer tracks shipments", client.get("/api/shipments/track", headers=H))
show("Admin marks order shipped", client.patch(
     f"/api/admin/shipments/{order_id}", json={"status": "shipped"}, headers=AH))
notifications = client.get("/api/notifications", headers=H)
show("Customer receives shipment notification", notifications)
notification_data = notifications.get_json()
assert notifications.status_code == 200
assert notification_data["unread_count"] == 1
assert notification_data["items"][0]["order_id"] == order_id
notification_id = notification_data["items"][0]["notification_id"]

same_status = client.patch(
    f"/api/admin/shipments/{order_id}", json={"status": "shipped"}, headers=AH
)
show("Repeating the same status does not duplicate the notification", same_status)
assert same_status.status_code == 200
assert len(client.get("/api/notifications", headers=H).get_json()["items"]) == 1

marked_read = client.patch(
    f"/api/notifications/{notification_id}/read", headers=H
)
show("Customer marks notification read", marked_read)
assert marked_read.status_code == 200
assert client.get("/api/notifications", headers=H).get_json()["unread_count"] == 0
show("Admin invalid shipment status (expect 400)", client.patch(
     "/api/admin/shipments/1", json={"status": "teleported"}, headers=AH))
show("Admin shipment for missing order (expect 404)", client.patch(
     "/api/admin/shipments/999", json={"status": "shipped"}, headers=AH))
show("Customer re-tracks (status now shipped)", client.get(
     "/api/shipments/track", headers=H))

# --- Reports ---
show("Admin sales report", client.get("/api/admin/reports/sales", headers=AH))
show("Admin sales report bad date (expect 400)", client.get(
     "/api/admin/reports/sales?from=31-05-2026", headers=AH))
show("Admin low-stock report", client.get(
     "/api/admin/reports/low-stock", headers=AH))
show("Customer hits reports (expect 403)", client.get(
     "/api/admin/reports/sales", headers=H))

print("\n" + "=" * 55)
print("ALL SCENARIOS EXECUTED")
print("=" * 55)
