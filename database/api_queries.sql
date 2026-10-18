-- API query examples

-- Register user
INSERT INTO users (full_name, email, password, role)
VALUES (?, ?, ?, 'customer');

-- Login lookup. Password verification is performed against the stored hash
-- in the application service, never directly in SQL.
SELECT user_id, full_name, email, password, role
FROM users
WHERE lower(email) = lower(?);

-- Browse books
SELECT b.book_id, b.title, b.author, b.description, b.price, c.category_name, i.stock_quantity
FROM books b
JOIN categories c ON b.category_id = c.category_id
JOIN inventory i ON b.book_id = i.book_id;

-- Search books
SELECT b.book_id, b.title, b.author, b.description, b.price, c.category_name, i.stock_quantity
FROM books b
JOIN categories c ON b.category_id = c.category_id
JOIN inventory i ON b.book_id = i.book_id
WHERE b.title LIKE ? OR b.author LIKE ? OR c.category_name LIKE ?;

-- Add to cart
INSERT INTO cart_items (cart_id, book_id, quantity)
VALUES (?, ?, ?)
ON CONFLICT(cart_id, book_id)
DO UPDATE SET quantity = quantity + excluded.quantity;

-- Update cart quantity
UPDATE cart_items
SET quantity = ?
WHERE cart_id = ? AND book_id = ?;

-- Remove cart item
DELETE FROM cart_items
WHERE cart_id = ? AND book_id = ?;

-- View cart
SELECT ci.cart_item_id, b.book_id, b.title, ci.quantity, b.price,
       ci.quantity * b.price AS subtotal
FROM cart_items ci
JOIN books b ON ci.book_id = b.book_id
WHERE ci.cart_id = ?;

-- Create order
INSERT INTO orders (user_id, delivery_address, total_price, status)
VALUES (?, ?, ?, 'processing');

-- Add order item
INSERT INTO order_items (order_id, book_id, quantity, unit_price, subtotal)
VALUES (?, ?, ?, ?, ?);

-- Process payment
INSERT INTO payments (order_id, amount, payment_method, payment_status)
VALUES (?, ?, 'card', 'processed');

-- Generate invoice
INSERT INTO invoices (order_id, receipt_message)
VALUES (?, 'Payment processed successfully. Invoice and receipt generated.');

-- Create shipment
INSERT INTO shipments (order_id, tracking_number, shipment_status, eta)
VALUES (?, ?, 'pending', ?);

-- Track order
SELECT o.order_id, o.status, s.tracking_number, s.shipment_status, s.eta
FROM orders o
JOIN shipments s ON o.order_id = s.order_id
WHERE o.user_id = ?;

-- Sales report
SELECT * FROM sales_report_view;
