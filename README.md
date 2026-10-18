# BookShop Frontend

Responsive HTML, CSS, and JavaScript interface for the BookShop project. The Flask application serves this directory in deployed and standard local operation; do not open the HTML files directly from the filesystem.

The interface provides a customer catalogue, cart, checkout, and order-tracking flow, plus a role-protected admin dashboard for catalogue management, stock updates, shipments, and reports.

```bash
cd BookShop
backend/venv/bin/python backend/server.py
```

Open `http://127.0.0.1:5001`. The interface uses the API on the same origin, so no
frontend port or API hostname is hardcoded. A separate host can supply an `api-base`
meta tag and list its origin in `CORS_ORIGINS` when that deployment model is required.
