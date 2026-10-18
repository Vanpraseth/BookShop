function getCurrentUser() {
    const userText = localStorage.getItem("user");
    if (!userText) return null;

    try {
        return JSON.parse(userText);
    } catch (error) {
        localStorage.removeItem("user");
        return null;
    }
}

function safeText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

let notificationTimer;
let newestNotificationId = null;

function notificationHeaders() {
    return { Authorization: `Bearer ${localStorage.getItem("token") || ""}` };
}

function formatNotificationDate(value) {
    if (!value) return "";
    const parsed = new Date(String(value).replace(" ", "T") + "Z");
    return Number.isNaN(parsed.getTime())
        ? value
        : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(parsed);
}

function renderNotifications(data) {
    const list = document.querySelector(".notification-list");
    const badge = document.querySelector(".notification-badge");
    if (!list || !badge) return;

    const items = Array.isArray(data.items) ? data.items : [];
    const unreadCount = Number(data.unread_count || 0);
    badge.textContent = unreadCount > 99 ? "99+" : String(unreadCount);
    badge.hidden = unreadCount === 0;
    list.innerHTML = items.length
        ? items.map(item => `
            <button class="notification-item ${item.read_at ? "" : "unread"}" type="button" data-notification-id="${Number(item.notification_id)}">
                <span>${safeText(item.message)}</span>
                <time>${safeText(formatNotificationDate(item.created_at))}</time>
            </button>`).join("")
        : `<p class="notification-empty">No notifications yet.</p>`;

    const latest = items[0];
    if (newestNotificationId !== null && latest && Number(latest.notification_id) > newestNotificationId) {
        showNotificationToast(latest.message);
        if (typeof window.loadOrders === "function") window.loadOrders();
    }
    newestNotificationId = latest ? Number(latest.notification_id) : newestNotificationId;
}

function showNotificationToast(message) {
    let toast = document.querySelector(".notification-toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.className = "notification-toast";
        toast.setAttribute("role", "status");
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(showNotificationToast.timeout);
    showNotificationToast.timeout = window.setTimeout(() => toast.classList.remove("visible"), 5000);
}

async function loadNotifications() {
    try {
        const response = await fetch(`${API_BASE}/notifications`, { headers: notificationHeaders() });
        if (!response.ok) return;
        renderNotifications(await response.json());
    } catch (error) {
        console.warn("Notifications are temporarily unavailable.");
    }
}

async function markNotificationRead(notificationId) {
    const response = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
        method: "PATCH",
        headers: notificationHeaders()
    });
    if (response.ok || response.status === 404) await loadNotifications();
}

async function markAllNotificationsRead() {
    const response = await fetch(`${API_BASE}/notifications/read-all`, {
        method: "PATCH",
        headers: notificationHeaders()
    });
    if (response.ok) await loadNotifications();
}

async function initializeNotificationCenter() {
    window.clearInterval(notificationTimer);
    await loadAppConfig();
    await loadNotifications();
    notificationTimer = window.setInterval(
        loadNotifications,
        APP_CONFIG.notificationPollSeconds * 1000
    );
}

function stopNotificationCenter() {
    window.clearInterval(notificationTimer);
    notificationTimer = undefined;
    newestNotificationId = null;
}

function updateAuthUI() {
    const authBox = document.querySelector(".auth");
    if (!authBox) return;

    const token = localStorage.getItem("token");
    const user = getCurrentUser();
    const isLoginPage = window.location.pathname.includes("login-register");

    if (token && user) {
        const destination = user.role === "admin" ? "admin.html?v=13" : "index.html?v=13";
        if (isLoginPage) {
            window.location.replace(destination);
            return;
        }

        if (user.role === "admin") {
            window.location.replace("admin.html?v=13");
            return;
        }

        const fullName = user.full_name || user.name || "Reader";
        const firstName = fullName.trim().split(/\s+/)[0];
        authBox.innerHTML = `
            <a class="orders-link" href="orders.html?v=13">My orders</a>
            <div class="notification-center">
                <button class="notification-button" type="button" aria-label="Notifications" aria-expanded="false">
                    <span aria-hidden="true">●</span>
                    <span class="notification-badge" hidden>0</span>
                </button>
                <section class="notification-panel" aria-label="Notifications" hidden>
                    <div class="notification-panel-heading"><strong>Notifications</strong><button class="mark-all-notifications" type="button">Mark all read</button></div>
                    <div class="notification-list"><p class="notification-empty">Loading notifications…</p></div>
                </section>
            </div>
            <div class="user-summary customer-user">
                <span class="user-avatar">${safeText(firstName.charAt(0).toUpperCase())}</span>
                <strong class="user-name">${safeText(firstName)}</strong>
            </div>
            <button class="logout-link" type="button">Sign out</button>
        `;

        authBox.querySelector(".logout-link").addEventListener("click", () => {
            stopNotificationCenter();
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.location.href = "index.html?v=13";
        });
        const notificationButton = authBox.querySelector(".notification-button");
        const notificationPanel = authBox.querySelector(".notification-panel");
        notificationButton.addEventListener("click", () => {
            notificationPanel.hidden = !notificationPanel.hidden;
            notificationButton.setAttribute("aria-expanded", String(!notificationPanel.hidden));
            if (!notificationPanel.hidden) loadNotifications();
        });
        authBox.querySelector(".notification-list").addEventListener("click", event => {
            const item = event.target.closest("[data-notification-id]");
            if (item) markNotificationRead(item.dataset.notificationId);
        });
        authBox.querySelector(".mark-all-notifications").addEventListener("click", markAllNotificationsRead);
        initializeNotificationCenter().catch(() => {
            console.warn("Notifications are temporarily unavailable.");
        });
        return;
    }

    stopNotificationCenter();

    if (isLoginPage) {
        authBox.innerHTML = `<a class="text-link" href="index.html?v=13">Browse books</a>`;
        return;
    }

    authBox.innerHTML = `
        <a class="text-link" href="login-register.html?v=13">Sign in</a>
        <a class="button button-small" href="login-register.html?v=13#register">Create account</a>
    `;
}

updateAuthUI();
document.addEventListener("DOMContentLoaded", updateAuthUI);
window.addEventListener("pageshow", updateAuthUI);
