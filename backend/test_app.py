import atexit
import os
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

BOOT_DIRECTORY = tempfile.TemporaryDirectory(prefix="bookshop-test-boot-")
atexit.register(BOOT_DIRECTORY.cleanup)
os.environ.update(
    {
        "APP_ENV": "testing",
        "SECRET_KEY": "integration-test-secret",
        "BOOKSHOP_DB": str(Path(BOOT_DIRECTORY.name) / "boot.db"),
        "ADMIN_NAME": "Integration Admin",
        "ADMIN_EMAIL": "integration-admin@example.test",
        "ADMIN_PASSWORD": "integration-admin-password",
    }
)

import db
import server


class BookShopIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="bookshop-test-")
        db.DB_PATH = Path(self.directory.name) / "bookshop.db"
        self.app = server.create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def database_row(self, query, parameters=()):
        with sqlite3.connect(db.DB_PATH) as connection:
            return connection.execute(query, parameters).fetchone()

    def register_customer(self, email="reader@example.test"):
        response = self.client.post(
            "/api/auth/register",
            json={
                "full_name": "Test Reader",
                "email": email,
                "password": "reader-password",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def login(self, email="reader@example.test", password="reader-password"):
        response = self.client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.get_json()['token']}"}

    def customer_headers(self, email="reader@example.test"):
        self.register_customer(email)
        return self.login(email)

    def admin_headers(self):
        return self.login(
            "integration-admin@example.test", "integration-admin-password"
        )

    def place_order(self):
        headers = self.customer_headers()
        added = self.client.post(
            "/api/cart/items",
            json={"book_id": 1, "quantity": 2},
            headers=headers,
        )
        self.assertEqual(added.status_code, 200)
        checkout = self.client.post(
            "/api/orders",
            json={"delivery_address": "10 Test Street, Melbourne VIC 3000"},
            headers=headers,
        )
        self.assertEqual(checkout.status_code, 201)
        return headers, checkout.get_json()["order_id"]

    def test_public_catalogue_config_and_security_headers(self):
        homepage = self.client.get("/")
        self.assertEqual(homepage.status_code, 200)
        self.assertIn(b"BookShop", homepage.data)
        self.assertEqual(homepage.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(homepage.headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", homepage.headers["Content-Security-Policy"])
        homepage.close()

        health = self.client.get("/api/health")
        self.assertEqual(health.get_json(), {"status": "ok"})
        self.assertEqual(health.headers["Cache-Control"], "no-store")

        config = self.client.get("/api/config")
        self.assertEqual(config.status_code, 200)
        self.assertEqual(config.get_json()["application_name"], "BookShop")
        self.assertEqual(config.get_json()["currency_code"], "AUD")

        categories = self.client.get("/api/categories")
        self.assertEqual(categories.status_code, 200)
        self.assertEqual(len(categories.get_json()), 4)

        books = self.client.get("/api/books")
        self.assertEqual(books.status_code, 200)
        self.assertEqual(len(books.get_json()), 13)
        self.assertEqual(self.client.get("/api/books/1").status_code, 200)
        self.assertEqual(self.client.get("/api/books/999").status_code, 404)
        search = self.client.get("/api/books?q=security")
        self.assertTrue(search.get_json())
        self.assertTrue(
            all(
                "security" in (
                    f"{book['title']} {book['author']} {book['category_name']}"
                ).lower()
                for book in search.get_json()
            )
        )

    def test_frontend_local_asset_links_resolve(self):
        frontend = PROJECT_ROOT / "frontend"
        for page in frontend.glob("*.html"):
            content = page.read_text(encoding="utf-8")
            self.assertIn("BookShop", content, page.name)
            for reference in re.findall(r'(?:src|href)="([^"]+)"', content):
                local_reference = reference.split("#", 1)[0].split("?", 1)[0]
                if not local_reference or "://" in local_reference:
                    continue
                with self.subTest(page=page.name, reference=reference):
                    self.assertTrue(
                        (frontend / local_reference).is_file(),
                        f"{page.name} links to missing file {local_reference}",
                    )

    def test_registration_login_validation_and_password_storage(self):
        registered = self.register_customer()
        self.assertEqual(registered["role"], "customer")
        self.assertNotIn("password", registered)

        stored = self.database_row(
            "SELECT full_name, email, password FROM users WHERE email = ?",
            ("reader@example.test",),
        )
        self.assertEqual(stored[:2], ("Test Reader", "reader@example.test"))
        self.assertNotEqual(stored[2], "reader-password")
        self.assertTrue(stored[2].startswith("pbkdf2_sha256$"))

        duplicate = self.client.post(
            "/api/auth/register",
            json={
                "full_name": "Another Reader",
                "email": "READER@example.test",
                "password": "another-password",
            },
        )
        self.assertEqual(duplicate.status_code, 400)

        invalid_payloads = [
            {"full_name": "", "email": "valid@example.test", "password": "password1"},
            {"full_name": "Reader", "email": "bad-email", "password": "password1"},
            {"full_name": "Reader", "email": "valid@example.test", "password": "short"},
            {"full_name": "R" * 121, "email": "valid@example.test", "password": "password1"},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assertEqual(
                    self.client.post("/api/auth/register", json=payload).status_code,
                    400,
                )

        self.assertEqual(
            self.client.post(
                "/api/auth/login",
                json={"email": "reader@example.test", "password": "wrong"},
            ).status_code,
            401,
        )
        self.assertEqual(self.client.get("/api/cart").status_code, 401)
        self.assertEqual(
            self.client.get(
                "/api/cart", headers={"Authorization": "Bearer invalid-token"}
            ).status_code,
            401,
        )

    def test_cart_validation_stock_limits_and_idempotent_remove(self):
        headers = self.customer_headers()
        invalid_quantities = [0, -1, 1.5, True, "not-a-number"]
        for quantity in invalid_quantities:
            with self.subTest(quantity=quantity):
                response = self.client.post(
                    "/api/cart/items",
                    json={"book_id": 1, "quantity": quantity},
                    headers=headers,
                )
                self.assertEqual(response.status_code, 400)

        self.assertEqual(
            self.client.post(
                "/api/cart/items",
                json={"book_id": 999, "quantity": 1},
                headers=headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/api/cart/items",
                json={"book_id": 4, "quantity": 1},
                headers=headers,
            ).status_code,
            200,
        )
        cumulative = self.client.post(
            "/api/cart/items",
            json={"book_id": 4, "quantity": 2},
            headers=headers,
        )
        self.assertEqual(cumulative.status_code, 409)
        cart = self.client.get("/api/cart", headers=headers).get_json()
        self.assertEqual(cart["items"][0]["quantity"], 1)

        missing_update = self.client.patch(
            "/api/cart/items/3", json={"quantity": 1}, headers=headers
        )
        self.assertEqual(missing_update.status_code, 404)
        self.assertEqual(
            self.client.delete("/api/cart/items/999", headers=headers).status_code,
            200,
        )

    def test_checkout_persists_related_records_and_enforces_ownership(self):
        headers, order_id = self.place_order()
        order = self.client.get(f"/api/orders/{order_id}", headers=headers)
        self.assertEqual(order.status_code, 200)
        self.assertEqual(order.get_json()["shipment_status"], "pending")
        self.assertEqual(len(order.get_json()["items"]), 1)

        self.assertEqual(
            self.database_row(
                "SELECT status, delivery_address FROM orders WHERE order_id = ?",
                (order_id,),
            ),
            ("paid", "10 Test Street, Melbourne VIC 3000"),
        )
        self.assertEqual(
            self.database_row(
                "SELECT payment_status FROM payments WHERE order_id = ?", (order_id,)
            ),
            ("processed",),
        )
        self.assertIsNotNone(
            self.database_row("SELECT invoice_id FROM invoices WHERE order_id = ?", (order_id,))
        )
        self.assertIsNotNone(
            self.database_row("SELECT shipment_id FROM shipments WHERE order_id = ?", (order_id,))
        )
        self.assertEqual(
            self.database_row("SELECT stock_quantity FROM inventory WHERE book_id = 1"),
            (8,),
        )
        self.assertEqual(self.database_row("SELECT COUNT(*) FROM cart_items"), (0,))

        empty_checkout = self.client.post(
            "/api/orders",
            json={"delivery_address": "10 Test Street"},
            headers=headers,
        )
        self.assertEqual(empty_checkout.status_code, 400)

        other_headers = self.customer_headers("other-reader@example.test")
        self.assertEqual(
            self.client.get(f"/api/orders/{order_id}", headers=other_headers).status_code,
            404,
        )

    def test_checkout_rolls_back_when_stock_changes_after_cart_add(self):
        headers = self.customer_headers()
        self.assertEqual(
            self.client.post(
                "/api/cart/items",
                json={"book_id": 4, "quantity": 2},
                headers=headers,
            ).status_code,
            200,
        )
        with sqlite3.connect(db.DB_PATH) as connection:
            connection.execute(
                "UPDATE inventory SET stock_quantity = 1 WHERE book_id = 4"
            )
        checkout = self.client.post(
            "/api/orders",
            json={"delivery_address": "10 Test Street"},
            headers=headers,
        )
        self.assertEqual(checkout.status_code, 409)
        self.assertEqual(self.database_row("SELECT COUNT(*) FROM orders"), (0,))
        self.assertEqual(self.database_row("SELECT COUNT(*) FROM payments"), (0,))
        self.assertEqual(self.database_row("SELECT COUNT(*) FROM cart_items"), (1,))
        self.assertEqual(
            self.database_row("SELECT stock_quantity FROM inventory WHERE book_id = 4"),
            (1,),
        )

    def test_shipment_updates_create_owned_persistent_notifications(self):
        customer_headers, order_id = self.place_order()
        admin_headers = self.admin_headers()

        empty = self.client.get("/api/notifications", headers=customer_headers)
        self.assertEqual(empty.get_json(), {"items": [], "unread_count": 0})

        packed = self.client.patch(
            f"/api/admin/shipments/{order_id}",
            json={"status": "packed"},
            headers=admin_headers,
        )
        self.assertEqual(packed.status_code, 200)
        self.assertEqual(packed.get_json()["shipment_status"], "packed")

        notifications = self.client.get(
            "/api/notifications", headers=customer_headers
        ).get_json()
        self.assertEqual(notifications["unread_count"], 1)
        self.assertEqual(notifications["items"][0]["order_id"], order_id)
        notification_id = notifications["items"][0]["notification_id"]

        duplicate = self.client.patch(
            f"/api/admin/shipments/{order_id}",
            json={"status": "packed"},
            headers=admin_headers,
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(
            len(self.client.get("/api/notifications", headers=customer_headers).get_json()["items"]),
            1,
        )

        other_headers = self.customer_headers("other-reader@example.test")
        self.assertEqual(
            self.client.patch(
                f"/api/notifications/{notification_id}/read", headers=other_headers
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.patch(
                f"/api/notifications/{notification_id}/read", headers=customer_headers
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/notifications", headers=customer_headers).get_json()["unread_count"],
            0,
        )

        self.client.patch(
            f"/api/admin/shipments/{order_id}",
            json={"status": "shipped"},
            headers=admin_headers,
        )
        read_all = self.client.patch(
            "/api/notifications/read-all", headers=customer_headers
        )
        self.assertEqual(read_all.status_code, 200)
        self.assertEqual(read_all.get_json()["updated"], 1)

    def test_admin_permissions_and_catalogue_validation(self):
        customer_headers = self.customer_headers()
        admin_headers = self.admin_headers()
        self.assertEqual(
            self.client.get(
                "/api/admin/reports/sales", headers=customer_headers
            ).status_code,
            403,
        )

        valid_book = {
            "title": "Integration Testing",
            "author": "Test Author",
            "description": "A test book.",
            "price": 35.5,
            "category_id": 1,
            "stock": 6,
        }
        added = self.client.post(
            "/api/admin/books", json=valid_book, headers=admin_headers
        )
        self.assertEqual(added.status_code, 201)
        book_id = added.get_json()["book_id"]

        invalid_category = {**valid_book, "category_id": 999}
        self.assertEqual(
            self.client.post(
                "/api/admin/books", json=invalid_category, headers=admin_headers
            ).status_code,
            400,
        )
        fractional_stock = self.client.patch(
            f"/api/admin/books/{book_id}/stock",
            json={"quantity": 1.5},
            headers=admin_headers,
        )
        self.assertEqual(fractional_stock.status_code, 400)

        valid_book["title"] = "Integration Testing Revised"
        edited = self.client.put(
            f"/api/admin/books/{book_id}", json=valid_book, headers=admin_headers
        )
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.get_json()["title"], "Integration Testing Revised")
        self.assertEqual(
            self.client.patch(
                f"/api/admin/books/{book_id}/stock",
                json={"quantity": 9},
                headers=admin_headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(
                f"/api/admin/books/{book_id}", headers=admin_headers
            ).status_code,
            200,
        )

        self.assertEqual(
            self.client.get(
                "/api/admin/reports/sales?from=16-10-2026", headers=admin_headers
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(
                "/api/admin/reports/low-stock", headers=admin_headers
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.patch(
                "/api/admin/shipments/999",
                json={"status": "shipped"},
                headers=admin_headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.patch(
                "/api/admin/shipments/999",
                json={"status": "teleported"},
                headers=admin_headers,
            ).status_code,
            400,
        )

    def test_existing_database_receives_notification_migration(self):
        with sqlite3.connect(db.DB_PATH) as connection:
            connection.execute("DROP TABLE notifications")
        self.assertIsNone(
            self.database_row(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"
            )
        )
        db.initialize_database()
        self.assertEqual(
            self.database_row(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"
            ),
            ("notifications",),
        )

    def test_production_requires_secret_key(self):
        original_environment = os.environ.get("APP_ENV")
        original_secret = os.environ.pop("SECRET_KEY", None)
        os.environ["APP_ENV"] = "production"
        try:
            with self.assertRaises(RuntimeError):
                server.create_app()
        finally:
            os.environ["APP_ENV"] = original_environment or "testing"
            if original_secret is not None:
                os.environ["SECRET_KEY"] = original_secret


if __name__ == "__main__":
    unittest.main(verbosity=2)
