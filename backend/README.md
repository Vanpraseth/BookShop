# BookShop Backend API

## Built With
Python 3, Flask, Flask-CORS, Gunicorn, and SQLite

## How to Run

1. Install dependencies: pip install -r requirements.txt

2. Start the local server: python server.py

3. API runs at http://127.0.0.1:5001

4. To test all endpoints with a temporary database: python test_api.py

For production, use the root `Dockerfile` or `Procfile`. Set `APP_ENV=production`, provide a private `SECRET_KEY`, and attach persistent storage for `BOOKSHOP_DB`.

Customer accounts are created through registration. An initial administrator can be
created with the private `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_NAME`
environment variables. No shared credentials are stored in the repository.

## Endpoints

Public
POST   /api/auth/register       Create a new customer account
POST   /api/auth/login          Login and receive a token
GET    /api/books               Browse all books, add ?q= to search by keyword
GET    /api/books/{id}          Get details of a single book
GET    /api/categories          List book categories
GET    /api/config              Public display and workflow configuration

Customer
GET    /api/cart                        View current cart
POST   /api/cart/items                  Add a book to cart
PATCH  /api/cart/items/{book_id}        Update quantity (set 0 to remove)
DELETE /api/cart/items/{book_id}        Remove a book from cart
POST   /api/orders                      Checkout and place order
GET    /api/orders                      View order history
GET    /api/orders/{id}                 View a specific order and shipment
GET    /api/shipments/track             Track all shipments
GET    /api/notifications               List notifications and unread count
PATCH  /api/notifications/{id}/read     Mark one notification read
PATCH  /api/notifications/read-all      Mark all notifications read

Admin
POST   /api/admin/books                     Add a new book
PUT    /api/admin/books/{id}                Edit a book
DELETE /api/admin/books/{id}                Delete a book
PATCH  /api/admin/books/{id}/stock          Update stock quantity
PATCH  /api/admin/shipments/{order_id}      Update shipment status
GET    /api/admin/reports/sales             Sales report, add ?from=&to= for date range
GET    /api/admin/reports/low-stock         Books below stock threshold
