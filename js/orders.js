function ordersUser() {
    try { return JSON.parse(localStorage.getItem("user") || "null"); }
    catch (error) { return null; }
}

function escapeOrderText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function requireCustomer() {
    const user = ordersUser();
    const token = localStorage.getItem("token");
    if (!token || !user) {
        window.location.replace("login-register.html?v=13");
        return false;
    }
    if (user.role === "admin") {
        window.location.replace("admin.html?v=13");
        return false;
    }
    return true;
}

function expireOrdersSession() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.replace("login-register.html?v=13");
}

async function orderRequest(path) {
    const response = await fetch(`${API_BASE}${path}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` }
    });
    const text = await response.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch (error) { data = { error: text || "Invalid server response." }; }
    if (response.status === 401) {
        expireOrdersSession();
        throw new Error("Your session expired.");
    }
    if (!response.ok) throw new Error(data.error || "Could not load your orders.");
    return data;
}

function setOrderNotice(message, type = "") {
    const notice = document.getElementById("order-notice");
    notice.textContent = message;
    notice.className = `order-notice ${type}`.trim();
}

function formatOrderDate(value) {
    if (!value) return "Date unavailable";
    const parsed = new Date(String(value).replace(" ", "T") + (String(value).includes("Z") ? "" : "Z"));
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(parsed);
}

function progressMarkup(status) {
    const current = Math.max(0, APP_CONFIG.shipmentStatuses.indexOf(status));
    return `<div class="tracking-progress" aria-label="Shipment progress">${APP_CONFIG.shipmentStatuses.map((step, index) =>
        `<span class="progress-step ${index <= current ? "complete" : ""}">${step}</span>`
    ).join("")}</div>`;
}

function renderOrders(orders) {
    const list = document.getElementById("orders-list");
    if (!orders.length) {
        list.innerHTML = `<div class="orders-empty"><h2>No orders yet</h2><p>Your completed purchases will appear here.</p><a class="button" href="index.html?v=13">Browse books</a></div>`;
        return;
    }

    list.innerHTML = orders.map((order, index) => {
        const shipmentStatus = order.shipment?.shipment_status || APP_CONFIG.shipmentStatuses[0];
        const items = Array.isArray(order.items) ? order.items : [];
        return `
            <details class="order-card" ${index === 0 ? "open" : ""}>
                <summary class="order-summary">
                    <span class="order-identity"><strong>Order #${Number(order.order_id)}</strong><time datetime="${escapeOrderText(order.created_at || "")}">${escapeOrderText(formatOrderDate(order.created_at))}</time></span>
                    <span class="order-summary-meta"><strong class="summary-total">${formatMoney(order.total_price)}</strong><span class="status-badge ${shipmentStatus === "delivered" ? "delivered" : ""}">${escapeOrderText(shipmentStatus.replace("_", " "))}</span><span class="order-chevron" aria-hidden="true">⌄</span></span>
                </summary>
                <div class="order-body">
                    <div class="order-items">
                        <h3>Books</h3>
                        ${items.map(item => `<div class="order-item"><div><strong>${escapeOrderText(item.title)}</strong><small>Quantity ${Number(item.quantity)}</small></div><span class="order-item-price">${formatMoney(item.subtotal)}</span></div>`).join("") || `<p class="loading-copy">Item details unavailable.</p>`}
                    </div>
                    <div class="delivery-summary">
                        <h3>Delivery</h3>
                        <dl class="delivery-detail">
                            <dt>Tracking</dt><dd>${escapeOrderText(order.shipment?.tracking_number || "Preparing shipment")}</dd>
                            <dt>ETA</dt><dd>${escapeOrderText(order.shipment?.eta || "To be confirmed")}</dd>
                            <dt>Address</dt><dd>${escapeOrderText(order.delivery_address)}</dd>
                        </dl>
                        ${progressMarkup(shipmentStatus)}
                    </div>
                </div>
            </details>`;
    }).join("");

    list.querySelectorAll("details.order-card").forEach(card => {
        card.addEventListener("toggle", () => {
            if (!card.open) return;
            list.querySelectorAll("details.order-card[open]").forEach(other => {
                if (other !== card) other.open = false;
            });
        });
    });
}

async function loadOrders(showRefreshMessage = false) {
    const button = document.getElementById("refresh-orders");
    button.disabled = true;
    try {
        await loadAppConfig();
        const [history, shipments] = await Promise.all([
            orderRequest("/orders"),
            orderRequest("/shipments/track")
        ]);
        const shipmentByOrder = new Map(shipments.map(shipment => [Number(shipment.order_id), shipment]));
        const detailedOrders = await Promise.all(history.map(async order => {
            try {
                const detail = await orderRequest(`/orders/${Number(order.order_id)}`);
                return { ...order, ...detail, shipment: shipmentByOrder.get(Number(order.order_id)) };
            } catch (error) {
                return { ...order, shipment: shipmentByOrder.get(Number(order.order_id)), items: [] };
            }
        }));
        renderOrders(detailedOrders);
        if (showRefreshMessage) setOrderNotice("Order information refreshed.");
    } catch (error) {
        setOrderNotice(error.message || "Could not load your orders.", "error");
        document.getElementById("orders-list").innerHTML = `<div class="orders-empty"><p>Order information is currently unavailable.</p></div>`;
        console.error(error);
    } finally {
        button.disabled = false;
    }
}

window.loadOrders = loadOrders;

document.addEventListener("DOMContentLoaded", () => {
    if (!requireCustomer()) return;
    const placedOrder = new URLSearchParams(window.location.search).get("placed");
    if (placedOrder) setOrderNotice(`Order #${placedOrder} was placed successfully.`);
    document.getElementById("refresh-orders").addEventListener("click", () => loadOrders(true));
    loadOrders();
});
