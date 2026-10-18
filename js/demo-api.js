(function initializeBookShopDemo() {
    const query = new URLSearchParams(window.location.search);
    if (query.get("demo") === "1") sessionStorage.setItem("bookshop.demo.enabled", "1");

    const demoMode = window.location.hostname.endsWith("github.io")
        || sessionStorage.getItem("bookshop.demo.enabled") === "1";
    window.BOOKSHOP_DEMO_MODE = demoMode;
    if (!demoMode) return;

    const STATE_KEY = "bookshop.demo.state.v1";
    const DEMO_USERS = {
        customer: {
            user_id: 1,
            full_name: "Demo Shopper",
            email: "shopper@bookshop.demo",
            role: "customer"
        },
        admin: {
            user_id: 2,
            full_name: "Demo Administrator",
            email: "administrator@bookshop.demo",
            role: "admin"
        }
    };

    const CATEGORIES = [
        { category_id: 1, category_name: "Programming" },
        { category_id: 2, category_name: "Cybersecurity" },
        { category_id: 3, category_name: "Business" },
        { category_id: 4, category_name: "Fiction" }
    ];

    const BOOKS = [
        { book_id: 1, title: "Python Basics", author: "John Smith", description: "A practical introduction to Python programming and problem solving.", price: 49.99, category_id: 1, category_name: "Programming", stock_quantity: 10, low_stock_threshold: 3 },
        { book_id: 2, title: "Network Security", author: "Alice Brown", description: "An accessible guide to network security concepts and defensive practices.", price: 69.99, category_id: 2, category_name: "Cybersecurity", stock_quantity: 5, low_stock_threshold: 3 },
        { book_id: 3, title: "Business Strategy", author: "Mark Lee", description: "Frameworks and practical tools for building a focused business strategy.", price: 39.99, category_id: 3, category_name: "Business", stock_quantity: 8, low_stock_threshold: 3 },
        { book_id: 4, title: "The Silent Library", author: "Emma White", description: "A mystery unfolding among the forgotten shelves of an old bookstore.", price: 24.99, category_id: 4, category_name: "Fiction", stock_quantity: 2, low_stock_threshold: 3 },
        { book_id: 5, title: "Clean Code", author: "Robert C. Martin", description: "A handbook for writing readable and maintainable software.", price: 55.00, category_id: 1, category_name: "Programming", stock_quantity: 12, low_stock_threshold: 3 },
        { book_id: 6, title: "The Pragmatic Programmer", author: "David Thomas, Andrew Hunt", description: "Timeless lessons for improving software craftsmanship and professional practice.", price: 59.99, category_id: 1, category_name: "Programming", stock_quantity: 9, low_stock_threshold: 3 },
        { book_id: 7, title: "The Art of Invisibility", author: "Kevin Mitnick", description: "A guide to privacy, personal security, and reducing exposure online.", price: 34.99, category_id: 2, category_name: "Cybersecurity", stock_quantity: 6, low_stock_threshold: 3 },
        { book_id: 8, title: "Dune", author: "Frank Herbert", description: "An epic story of politics, belief, survival, and power on a desert planet.", price: 22.99, category_id: 4, category_name: "Fiction", stock_quantity: 8, low_stock_threshold: 3 }
    ];

    function initialState() {
        const placedAt = new Date(Date.now() - (2 * 24 * 60 * 60 * 1000)).toISOString();
        return {
            books: BOOKS.map(book => ({ ...book })),
            cart: [],
            orders: [{
                order_id: 1001,
                user_id: 1,
                delivery_address: "24 Demo Lane, Melbourne VIC 3000",
                total_price: 55,
                status: "shipped",
                created_at: placedAt,
                items: [{ book_id: 5, title: "Clean Code", quantity: 1, unit_price: 55, subtotal: 55 }],
                shipment: {
                    order_id: 1001,
                    tracking_number: "DEMO1001",
                    shipment_status: "shipped",
                    eta: "2-3 business days"
                }
            }],
            notifications: [{
                notification_id: 1,
                order_id: 1001,
                message: "Order #1001 shipment status changed to shipped.",
                created_at: placedAt,
                read_at: null
            }],
            nextBookId: 9,
            nextOrderId: 1002,
            nextNotificationId: 2
        };
    }

    function readState() {
        try {
            const parsed = JSON.parse(localStorage.getItem(STATE_KEY) || "null");
            if (parsed?.books && parsed?.orders && parsed?.notifications) return parsed;
        } catch (error) {
            console.warn("The demo state was reset because it could not be read.");
        }
        const state = initialState();
        writeState(state);
        return state;
    }

    function writeState(state) {
        localStorage.setItem(STATE_KEY, JSON.stringify(state));
    }

    function setRole(role) {
        const user = DEMO_USERS[role] || DEMO_USERS.customer;
        localStorage.setItem("token", `bookshop-demo-${user.role}`);
        localStorage.setItem("user", JSON.stringify(user));
        return user;
    }

    function currentUser() {
        try {
            const user = JSON.parse(localStorage.getItem("user") || "null");
            if (user?.role === "admin") return DEMO_USERS.admin;
        } catch (error) {
            // A clean customer session is restored below.
        }
        return DEMO_USERS.customer;
    }

    if (!localStorage.getItem("token") || !localStorage.getItem("user")) setRole("customer");
    readState();

    function json(data, status = 200) {
        return new Response(JSON.stringify(data), {
            status,
            headers: { "Content-Type": "application/json", "Cache-Control": "no-store" }
        });
    }

    function cartPayload(state) {
        const items = state.cart.map(entry => {
            const book = state.books.find(item => Number(item.book_id) === Number(entry.book_id));
            if (!book) return null;
            return {
                book_id: book.book_id,
                title: book.title,
                price: book.price,
                quantity: entry.quantity,
                subtotal: Number((book.price * entry.quantity).toFixed(2))
            };
        }).filter(Boolean);
        return {
            items,
            total: Number(items.reduce((sum, item) => sum + item.subtotal, 0).toFixed(2))
        };
    }

    async function requestBody(input, init) {
        const raw = init?.body || (input instanceof Request ? await input.clone().text() : "");
        if (!raw) return {};
        try { return JSON.parse(raw); } catch (error) { return {}; }
    }

    function categoryName(categoryId) {
        return CATEGORIES.find(category => Number(category.category_id) === Number(categoryId))?.category_name || "Uncategorised";
    }

    function salesReport(state) {
        const totals = new Map();
        state.orders.forEach(order => order.items.forEach(item => {
            const existing = totals.get(item.book_id) || { title: item.title, total_quantity_sold: 0, total_sales: 0 };
            existing.total_quantity_sold += Number(item.quantity);
            existing.total_sales = Number((existing.total_sales + Number(item.subtotal)).toFixed(2));
            totals.set(item.book_id, existing);
        }));
        return {
            summary: {
                order_count: state.orders.length,
                total_revenue: Number(state.orders.reduce((sum, order) => sum + Number(order.total_price), 0).toFixed(2))
            },
            best_sellers: [...totals.values()].sort((a, b) => b.total_quantity_sold - a.total_quantity_sold).slice(0, 5)
        };
    }

    async function handleDemoRequest(path, method, body) {
        const state = readState();

        if (path === "/config" && method === "GET") {
            return json({ application_name: "BookShop", currency_code: "AUD", shipment_statuses: ["pending", "packed", "shipped", "delivered"], notification_poll_seconds: 30 });
        }
        if (path === "/categories" && method === "GET") return json(CATEGORIES);
        if (path === "/books" && method === "GET") return json(state.books);

        const publicBook = path.match(/^\/books\/(\d+)$/);
        if (publicBook && method === "GET") {
            const book = state.books.find(item => Number(item.book_id) === Number(publicBook[1]));
            return book ? json(book) : json({ error: "Book not found." }, 404);
        }

        if (path === "/auth/register" && method === "POST") {
            const name = String(body.full_name || "Demo Shopper").trim();
            const email = String(body.email || DEMO_USERS.customer.email).trim();
            if (!name || !email.includes("@") || String(body.password || "").length < 8) {
                return json({ error: "Enter a name, valid email, and password of at least 8 characters." }, 400);
            }
            return json({ ...DEMO_USERS.customer, full_name: name, email }, 201);
        }

        if (path === "/auth/login" && method === "POST") {
            const role = String(body.email || "").toLowerCase().startsWith("admin") ? "admin" : "customer";
            const user = setRole(role);
            return json({ token: `bookshop-demo-${role}`, user });
        }

        if (path === "/cart" && method === "GET") return json(cartPayload(state));
        if (path === "/cart/items" && method === "POST") {
            const book = state.books.find(item => Number(item.book_id) === Number(body.book_id));
            const quantity = Number(body.quantity || 1);
            if (!book || !Number.isInteger(quantity) || quantity < 1) return json({ error: "Invalid cart item." }, 400);
            const existing = state.cart.find(item => Number(item.book_id) === Number(book.book_id));
            const requested = quantity + Number(existing?.quantity || 0);
            if (requested > Number(book.stock_quantity)) return json({ error: `Only ${book.stock_quantity} copies are available.` }, 409);
            if (existing) existing.quantity = requested;
            else state.cart.push({ book_id: book.book_id, quantity });
            writeState(state);
            return json(cartPayload(state), 201);
        }

        const cartItem = path.match(/^\/cart\/items\/(\d+)$/);
        if (cartItem && method === "DELETE") {
            state.cart = state.cart.filter(item => Number(item.book_id) !== Number(cartItem[1]));
            writeState(state);
            return json({ message: "Removed." });
        }
        if (cartItem && method === "PATCH") {
            const item = state.cart.find(entry => Number(entry.book_id) === Number(cartItem[1]));
            const quantity = Number(body.quantity);
            if (!item || !Number.isInteger(quantity) || quantity < 1) return json({ error: "Invalid quantity." }, 400);
            item.quantity = quantity;
            writeState(state);
            return json(cartPayload(state));
        }

        if (path === "/orders" && method === "POST") {
            const cart = cartPayload(state);
            const address = String(body.delivery_address || "").trim();
            if (!address) return json({ error: "Address required." }, 400);
            if (!cart.items.length) return json({ error: "Cart is empty." }, 400);
            const orderId = state.nextOrderId++;
            cart.items.forEach(item => {
                const book = state.books.find(candidate => Number(candidate.book_id) === Number(item.book_id));
                book.stock_quantity -= item.quantity;
            });
            const order = {
                order_id: orderId,
                user_id: 1,
                delivery_address: address,
                total_price: cart.total,
                status: "paid",
                created_at: new Date().toISOString(),
                items: cart.items.map(item => ({ ...item, unit_price: item.price })),
                shipment: { order_id: orderId, tracking_number: `DEMO${orderId}`, shipment_status: "pending", eta: "3-5 business days" }
            };
            state.orders.unshift(order);
            state.cart = [];
            state.notifications.unshift({ notification_id: state.nextNotificationId++, order_id: orderId, message: `Order #${orderId} was placed successfully.`, created_at: new Date().toISOString(), read_at: null });
            writeState(state);
            return json({ order_id: orderId, total_price: cart.total, status: "paid", message: "Demo order placed." }, 201);
        }
        if (path === "/orders" && method === "GET") return json(state.orders);

        const orderDetail = path.match(/^\/orders\/(\d+)$/);
        if (orderDetail && method === "GET") {
            const order = state.orders.find(item => Number(item.order_id) === Number(orderDetail[1]));
            return order ? json(order) : json({ error: "Order not found." }, 404);
        }
        if (path === "/shipments/track" && method === "GET") return json(state.orders.map(order => order.shipment));

        if (path === "/notifications" && method === "GET") {
            return json({ items: state.notifications, unread_count: state.notifications.filter(item => !item.read_at).length });
        }
        if (path === "/notifications/read-all" && method === "PATCH") {
            state.notifications.forEach(item => { if (!item.read_at) item.read_at = new Date().toISOString(); });
            writeState(state);
            return json({ message: "Notifications marked as read." });
        }
        const notification = path.match(/^\/notifications\/(\d+)\/read$/);
        if (notification && method === "PATCH") {
            const item = state.notifications.find(entry => Number(entry.notification_id) === Number(notification[1]));
            if (item) item.read_at = new Date().toISOString();
            writeState(state);
            return json({ message: "Notification marked as read." });
        }

        if (path === "/admin/reports/sales" && method === "GET") return json(salesReport(state));
        if (path === "/admin/reports/low-stock" && method === "GET") {
            return json(state.books.filter(book => Number(book.stock_quantity) <= Number(book.low_stock_threshold)));
        }
        if (path === "/admin/shipments" && method === "GET") {
            return json(state.orders.map(order => ({ ...order.shipment, total_price: order.total_price, created_at: order.created_at, customer_name: "Demo Shopper" })));
        }
        if (path === "/admin/books" && method === "POST") {
            const book = { book_id: state.nextBookId++, title: String(body.title || "").trim(), author: String(body.author || "").trim(), description: String(body.description || "").trim(), price: Number(body.price), category_id: Number(body.category_id), category_name: categoryName(body.category_id), stock_quantity: Number(body.stock || 0), low_stock_threshold: 3 };
            if (!book.title || !book.author || !Number.isFinite(book.price) || book.price <= 0) return json({ error: "Enter valid book details." }, 400);
            state.books.push(book);
            writeState(state);
            return json(book, 201);
        }

        const adminStock = path.match(/^\/admin\/books\/(\d+)\/stock$/);
        if (adminStock && method === "PATCH") {
            const book = state.books.find(item => Number(item.book_id) === Number(adminStock[1]));
            if (!book) return json({ error: "Book not found." }, 404);
            book.stock_quantity = Math.max(0, Number(body.quantity || 0));
            writeState(state);
            return json(book);
        }
        const adminBook = path.match(/^\/admin\/books\/(\d+)$/);
        if (adminBook && method === "PUT") {
            const book = state.books.find(item => Number(item.book_id) === Number(adminBook[1]));
            if (!book) return json({ error: "Book not found." }, 404);
            Object.assign(book, { title: String(body.title || book.title).trim(), author: String(body.author || book.author).trim(), description: String(body.description || "").trim(), price: Number(body.price), category_id: Number(body.category_id), category_name: categoryName(body.category_id) });
            writeState(state);
            return json(book);
        }
        if (adminBook && method === "DELETE") {
            state.books = state.books.filter(item => Number(item.book_id) !== Number(adminBook[1]));
            state.cart = state.cart.filter(item => Number(item.book_id) !== Number(adminBook[1]));
            writeState(state);
            return json({ message: "Deleted." });
        }
        const adminShipment = path.match(/^\/admin\/shipments\/(\d+)$/);
        if (adminShipment && method === "PATCH") {
            const order = state.orders.find(item => Number(item.order_id) === Number(adminShipment[1]));
            if (!order) return json({ error: "Shipment not found." }, 404);
            order.shipment.shipment_status = String(body.status || "pending");
            if (["shipped", "delivered"].includes(order.shipment.shipment_status)) order.status = order.shipment.shipment_status;
            state.notifications.unshift({ notification_id: state.nextNotificationId++, order_id: order.order_id, message: `Order #${order.order_id} shipment status changed to ${order.shipment.shipment_status}.`, created_at: new Date().toISOString(), read_at: null });
            writeState(state);
            return json(order.shipment);
        }

        return json({ error: "This action is not available in the static demo." }, 404);
    }

    const browserFetch = window.fetch.bind(window);
    window.fetch = async function demoFetch(input, init = {}) {
        const url = new URL(input instanceof Request ? input.url : input, window.location.href);
        const apiPosition = url.pathname.indexOf("/api");
        if (apiPosition === -1) return browserFetch(input, init);

        const path = url.pathname.slice(apiPosition + 4) || "/";
        const method = String(init.method || (input instanceof Request ? input.method : "GET")).toUpperCase();
        const body = await requestBody(input, init);
        await new Promise(resolve => window.setTimeout(resolve, 90));
        return handleDemoRequest(path, method, body);
    };

    document.addEventListener("DOMContentLoaded", () => {
        const banner = document.createElement("aside");
        banner.className = "demo-banner";
        banner.setAttribute("aria-label", "Demo controls");
        banner.innerHTML = `
            <span><strong>Interactive demo</strong> Changes are saved only in this browser.</span>
            <div>
                <button type="button" data-demo-role="customer">Customer view</button>
                <button type="button" data-demo-role="admin">Admin view</button>
                <button type="button" data-demo-reset>Reset demo</button>
            </div>`;
        document.body.prepend(banner);

        const role = currentUser().role;
        banner.querySelector(`[data-demo-role="${role}"]`)?.classList.add("active");
        banner.addEventListener("click", event => {
            const roleButton = event.target.closest("[data-demo-role]");
            if (roleButton) {
                const selectedRole = roleButton.dataset.demoRole;
                setRole(selectedRole);
                window.location.href = selectedRole === "admin" ? "admin.html" : "index.html";
                return;
            }
            if (event.target.closest("[data-demo-reset]")) {
                localStorage.removeItem(STATE_KEY);
                setRole("customer");
                window.location.href = "index.html";
            }
        });
    });
})();
