# BookShop Database

The application uses SQLite. The local `bookshop.db` file is excluded from Git because it can contain account, order, and delivery information.

## Included files

- schema.sql
- catalogue_data.sql
- api_queries.sql
- migrations/ (safe upgrades for an existing database)

## Tables

- users
- categories
- books
- inventory
- carts
- cart_items
- orders
- order_items
- payments
- invoices
- shipments
- notifications
- sales_report_view

## Supported features

1. Customer registration and login
2. Book browsing and searching
3. Book detail and stock display
4. Shopping cart add/update/delete
5. Checkout and order creation
6. Payment confirmation
7. Invoice and receipt generation
8. Shipment tracking
9. Inventory management
10. Sales reporting

## How to run

Open terminal in this folder and run:

```bash
sqlite3 bookshop.db
```

Then test:

```sql
.tables
SELECT * FROM books;
SELECT * FROM sales_report_view;
```

## Rebuild the local database

Run these commands from the `database` folder:

```bash
sqlite3 bookshop.db < schema.sql
sqlite3 bookshop.db < catalogue_data.sql
```

`catalogue_data.sql` contains catalogue records only. It contains no user accounts,
passwords, orders, or delivery addresses. Existing databases receive the idempotent
scripts in `migrations/` automatically when the application starts.
