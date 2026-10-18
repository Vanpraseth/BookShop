const ADMIN_API = `${API_BASE}/admin`;

let adminBooks = [];
let adminCategories = [];
let adminShipments = [];
let salesReport = { summary: {}, best_sellers: [] };
let lowStockBooks = [];
let editingBookId = null;

function adminUser() {
    try {
        return JSON.parse(localStorage.getItem("user") || "null");
    } catch (error) {
        return null;
    }
}

function escapeAdminText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function requireAdmin() {
    const user = adminUser();
    const token = localStorage.getItem("token");
    if (!token || !user) {
        window.location.replace("login-register.html?v=13");
        return null;
    }
    if (user.role !== "admin") {
        window.location.replace("index.html?v=13");
        return null;
    }
    return user;
}

function endSession() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.replace("login-register.html?v=13");
}

async function adminFetch(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${localStorage.getItem("token") || ""}`);
    if (options.body) headers.set("Content-Type", "application/json");

    const response = await fetch(`${ADMIN_API}${path}`, { ...options, headers });
    const text = await response.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch (error) { data = { error: text || "Invalid server response." }; }

    if (response.status === 401) {
        endSession();
        throw new Error("Your admin session expired.");
    }
    if (!response.ok) throw new Error(data.error || "The request could not be completed.");
    return data;
}

function setAdminMessage(message, type = "") {
    const element = document.getElementById("admin-message");
    element.textContent = message;
    element.className = `admin-message ${type}`.trim();
    window.clearTimeout(setAdminMessage.timeout);
    if (message) setAdminMessage.timeout = window.setTimeout(() => setAdminMessage(""), 4000);
}

function renderAdminIdentity(user) {
    const name = user.full_name || "Admin";
    document.getElementById("admin-name").textContent = name.split(/\s+/)[0];
    document.getElementById("admin-avatar").textContent = name.charAt(0).toUpperCase();
}

function categoryOptions() {
    return adminCategories.map(category => [
        Number(category.category_id), category.category_name
    ]);
}

function renderCategoryOptions(selectedId = "") {
    const select = document.getElementById("book-category");
    const categories = categoryOptions();
    select.innerHTML = categories.map(([id, name]) =>
        `<option value="${id}" ${Number(selectedId) === id ? "selected" : ""}>${escapeAdminText(name)}</option>`
    ).join("");
}

function renderMetrics() {
    const totalStock = adminBooks.reduce((sum, book) => sum + Number(book.stock_quantity || 0), 0);
    document.getElementById("metric-books").textContent = adminBooks.length;
    document.getElementById("metric-stock").textContent = totalStock;
    document.getElementById("metric-orders").textContent = Number(salesReport.summary?.order_count || 0);
    document.getElementById("metric-revenue").textContent = formatMoney(salesReport.summary?.total_revenue || 0);
}

function renderInventory() {
    const tbody = document.getElementById("inventory-body");
    const term = document.getElementById("inventory-search").value.trim().toLowerCase();
    const books = adminBooks.filter(book => `${book.title} ${book.author} ${book.category_name}`.toLowerCase().includes(term));

    if (!books.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="table-state">No matching books.</td></tr>`;
        return;
    }

    tbody.innerHTML = books.map(book => `
        <tr>
            <td class="book-cell"><strong>${escapeAdminText(book.title)}</strong><small>${escapeAdminText(book.author)}</small></td>
            <td>${escapeAdminText(book.category_name)}</td>
            <td>${formatMoney(book.price)}</td>
            <td>
                <div class="stock-control">
                    <input id="stock-${Number(book.book_id)}" type="number" min="0" step="1" value="${Number(book.stock_quantity)}" aria-label="Stock for ${escapeAdminText(book.title)}">
                    <button class="row-button" type="button" data-stock-id="${Number(book.book_id)}">Save</button>
                </div>
            </td>
            <td><div class="row-actions"><button class="row-button" type="button" data-edit-id="${Number(book.book_id)}">Edit</button><button class="row-button danger" type="button" data-delete-id="${Number(book.book_id)}">Delete</button></div></td>
        </tr>
    `).join("");
}

function renderShipments() {
    const tbody = document.getElementById("shipment-body");
    if (!adminShipments.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="table-state">No shipments yet.</td></tr>`;
        return;
    }
    tbody.innerHTML = adminShipments.map(shipment => `
        <tr>
            <td>#${Number(shipment.order_id)}</td>
            <td>${escapeAdminText(shipment.customer_name)}</td>
            <td>${escapeAdminText(shipment.tracking_number)}</td>
            <td>${formatMoney(shipment.total_price)}</td>
            <td><div class="shipment-control"><select id="shipment-${Number(shipment.order_id)}" aria-label="Shipment status for order ${Number(shipment.order_id)}">${APP_CONFIG.shipmentStatuses.map(status => `<option value="${status}" ${status === shipment.shipment_status ? "selected" : ""}>${status.replace("_", " ")}</option>`).join("")}</select></div></td>
            <td><button class="row-button" type="button" data-shipment-id="${Number(shipment.order_id)}">Update</button></td>
        </tr>
    `).join("");
}

function renderReports() {
    const best = document.getElementById("best-sellers");
    const low = document.getElementById("low-stock");
    const bestSellers = Array.isArray(salesReport.best_sellers) ? salesReport.best_sellers : [];

    best.innerHTML = bestSellers.length ? `<div class="report-list">${bestSellers.map(item => `
        <div class="report-row"><strong>${escapeAdminText(item.title)}</strong><span>${Number(item.total_quantity_sold)} sold · ${formatMoney(item.total_sales)}</span></div>
    `).join("")}</div>` : `<p class="table-state">No sales recorded yet.</p>`;

    low.innerHTML = lowStockBooks.length ? `<div class="report-list">${lowStockBooks.map(item => `
        <div class="report-row"><strong>${escapeAdminText(item.title)}</strong><span>${Number(item.stock_quantity)} left · threshold ${Number(item.low_stock_threshold)}</span></div>
    `).join("")}</div>` : `<p class="table-state">No books are below their stock threshold.</p>`;
}

async function loadAdminData(showMessage = false) {
    const button = document.getElementById("refresh-dashboard");
    button.disabled = true;
    try {
        await loadAppConfig();
        const [bookResponse, categories, report, lowStock, shipments] = await Promise.all([
            fetch(`${API_BASE}/books`).then(async response => {
                if (!response.ok) throw new Error("Could not load books.");
                return response.json();
            }),
            fetch(`${API_BASE}/categories`).then(async response => {
                if (!response.ok) throw new Error("Could not load categories.");
                return response.json();
            }),
            adminFetch("/reports/sales"),
            adminFetch("/reports/low-stock"),
            adminFetch("/shipments")
        ]);
        adminBooks = bookResponse;
        adminCategories = categories;
        salesReport = report;
        lowStockBooks = lowStock;
        adminShipments = shipments;
        renderCategoryOptions(editingBookId ? adminBooks.find(book => Number(book.book_id) === editingBookId)?.category_id : "");
        renderMetrics();
        renderInventory();
        renderShipments();
        renderReports();
        if (showMessage) setAdminMessage("Dashboard data refreshed.");
    } catch (error) {
        setAdminMessage(error.message || "Could not load the dashboard.", "error");
        console.error(error);
    } finally {
        button.disabled = false;
    }
}

function resetBookForm() {
    editingBookId = null;
    const form = document.getElementById("admin-book-form");
    form.reset();
    document.getElementById("book-form-title").textContent = "Add a book";
    document.getElementById("save-book").textContent = "Add book";
    document.getElementById("cancel-edit").hidden = true;
    renderCategoryOptions();
}

function editBook(id) {
    const book = adminBooks.find(item => Number(item.book_id) === Number(id));
    if (!book) return;
    editingBookId = Number(id);
    const form = document.getElementById("admin-book-form");
    form.elements.title.value = book.title;
    form.elements.author.value = book.author;
    form.elements.price.value = Number(book.price).toFixed(2);
    form.elements.stock.value = Number(book.stock_quantity);
    form.elements.description.value = book.description || "";
    renderCategoryOptions(book.category_id);
    document.getElementById("book-form-title").textContent = `Edit ${book.title}`;
    document.getElementById("save-book").textContent = "Save changes";
    document.getElementById("cancel-edit").hidden = false;
    document.getElementById("book-form").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function saveBook(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    const payload = {
        title: data.title.trim(), author: data.author.trim(), description: data.description.trim(),
        category_id: Number(data.category_id), price: Number(data.price), stock: Number(data.stock)
    };
    const button = document.getElementById("save-book");
    button.disabled = true;
    try {
        if (editingBookId) {
            await adminFetch(`/books/${editingBookId}`, { method: "PUT", body: JSON.stringify(payload) });
            await adminFetch(`/books/${editingBookId}/stock`, { method: "PATCH", body: JSON.stringify({ quantity: payload.stock }) });
            setAdminMessage("Book details updated.");
        } else {
            await adminFetch("/books", { method: "POST", body: JSON.stringify(payload) });
            setAdminMessage("Book added to the catalogue.");
        }
        resetBookForm();
        await loadAdminData();
    } catch (error) {
        setAdminMessage(error.message, "error");
    } finally {
        button.disabled = false;
    }
}

async function saveStock(id) {
    const input = document.getElementById(`stock-${id}`);
    try {
        await adminFetch(`/books/${id}/stock`, { method: "PATCH", body: JSON.stringify({ quantity: Number(input.value) }) });
        setAdminMessage("Stock quantity updated.");
        await loadAdminData();
    } catch (error) { setAdminMessage(error.message, "error"); }
}

async function deleteBook(id) {
    const book = adminBooks.find(item => Number(item.book_id) === Number(id));
    if (!book || !window.confirm(`Delete “${book.title}” from the catalogue?`)) return;
    try {
        await adminFetch(`/books/${id}`, { method: "DELETE" });
        setAdminMessage("Book deleted from the catalogue.");
        if (editingBookId === Number(id)) resetBookForm();
        await loadAdminData();
    } catch (error) { setAdminMessage(error.message, "error"); }
}

async function updateShipment(orderId) {
    const select = document.getElementById(`shipment-${orderId}`);
    try {
        await adminFetch(`/shipments/${orderId}`, { method: "PATCH", body: JSON.stringify({ status: select.value }) });
        setAdminMessage(`Shipment for order #${orderId} updated.`);
        await loadAdminData();
    } catch (error) { setAdminMessage(error.message, "error"); }
}

function attachAdminEvents() {
    document.getElementById("admin-logout").addEventListener("click", endSession);
    document.getElementById("refresh-dashboard").addEventListener("click", () => loadAdminData(true));
    document.getElementById("inventory-search").addEventListener("input", renderInventory);
    document.getElementById("admin-book-form").addEventListener("submit", saveBook);
    document.getElementById("cancel-edit").addEventListener("click", resetBookForm);
    document.getElementById("inventory-body").addEventListener("click", event => {
        const edit = event.target.closest("[data-edit-id]");
        const remove = event.target.closest("[data-delete-id]");
        const stock = event.target.closest("[data-stock-id]");
        if (edit) editBook(edit.dataset.editId);
        if (remove) deleteBook(remove.dataset.deleteId);
        if (stock) saveStock(stock.dataset.stockId);
    });
    document.getElementById("shipment-body").addEventListener("click", event => {
        const update = event.target.closest("[data-shipment-id]");
        if (update) updateShipment(update.dataset.shipmentId);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const user = requireAdmin();
    if (!user) return;
    renderAdminIdentity(user);
    attachAdminEvents();
    loadAdminData();
});
