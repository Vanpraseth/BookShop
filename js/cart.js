function getToken() {
    return localStorage.getItem("token");
}

function escapeCartText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function readJsonResponse(res) {
    const text = await res.text();
    try {
        return text ? JSON.parse(text) : {};
    } catch (error) {
        return { error: text || "Invalid server response" };
    }
}

function showToast(message, type = "success") {
    const toast = document.querySelector(".toast");
    if (!toast) {
        if (type === "error") alert(message);
        return;
    }

    toast.textContent = message;
    toast.className = `toast visible ${type === "error" ? "error" : ""}`;
    window.clearTimeout(showToast.timeout);
    showToast.timeout = window.setTimeout(() => { toast.className = "toast"; }, 2800);
}

function clearExpiredSession() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
}

async function fetchCart() {
    const token = getToken();
    if (!token) return { items: [], total: 0, loggedOut: true };

    try {
        const res = await fetch(`${API_BASE}/cart`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        const data = await readJsonResponse(res);

        if (res.status === 401) {
            clearExpiredSession();
            return { items: [], total: 0, loggedOut: true, error: "Your session expired." };
        }
        if (!res.ok) return { items: [], total: 0, error: data.error || "Unable to load your bag." };
        return data;
    } catch (error) {
        console.error("Cart request failed:", error);
        return { items: [], total: 0, error: "The bookstore service is currently unavailable." };
    }
}

function cartHeading() {
    return `<div class="cart-heading"><h2>Shopping Cart</h2></div>`;
}

function renderCart(cart) {
    const aside = document.querySelector(".right-aside");
    if (!aside) return;

    const items = Array.isArray(cart?.items) ? cart.items : [];
    const total = Number(cart?.total || 0);
    aside.innerHTML = cartHeading();

    if (cart?.loggedOut) {
        aside.innerHTML += `
            <div class="cart-empty">
                <span class="cart-empty-icon" aria-hidden="true">＋</span>
                <p>Your cart is waiting</p>
                <small>Sign in to add books and check out.</small>
            </div>
            <a class="button" href="login-register.html?v=13">Sign in to continue</a>`;
        return;
    }

    if (cart?.error) {
        aside.innerHTML += `<p class="empty-copy">${escapeCartText(cart.error)}</p>`;
        return;
    }

    if (items.length === 0) {
        aside.innerHTML += `
            <div class="cart-empty">
                <span class="cart-empty-icon" aria-hidden="true">＋</span>
                <p>Your cart is empty</p>
                <small>Add a book from the catalogue to begin.</small>
            </div>`;
        return;
    }

    aside.innerHTML += items.map(item => `
        <div class="cart-item">
            <div class="cart-item-head">
                <strong>${escapeCartText(item.title)}</strong>
                <button class="remove-button" type="button" data-remove-book="${Number(item.book_id)}">Remove</button>
            </div>
            <div class="cart-item-meta"><span>Quantity ${Number(item.quantity)}</span><span>${formatMoney(item.subtotal)}</span></div>
        </div>
    `).join("");

    const itemCount = items.reduce((sum, item) => sum + Number(item.quantity), 0);
    aside.innerHTML += `
        <div class="cart-summary">
            <div class="cart-summary-row"><span>${itemCount} ${itemCount === 1 ? "book" : "books"}</span><span>Included</span></div>
            <div class="cart-summary-row total"><span>Total</span><strong>${formatMoney(total)}</strong></div>
        </div>
        <a class="button" href="checkout.html?v=13">Go to checkout</a>`;
}

async function loadCart() {
    if (!document.querySelector(".right-aside")) return;
    await loadAppConfig();
    renderCart(await fetchCart());
}

async function addToCart(bookId, quantity = 1) {
    const token = getToken();
    if (!token) {
        showToast("Sign in before adding a book to your cart.", "error");
        window.setTimeout(() => { window.location.href = "login-register.html?v=13"; }, 800);
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/cart/items`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ book_id: Number(bookId), quantity: Number(quantity) })
        });
        const data = await readJsonResponse(res);

        if (res.status === 401) {
            clearExpiredSession();
            window.location.href = "login-register.html?v=13";
            return;
        }
        if (!res.ok) {
            showToast(data.error || "Could not add this book.", "error");
            return;
        }

        renderCart(data);
        showToast("Book added to your cart.");
    } catch (error) {
        showToast("Cannot connect to the bookstore service.", "error");
        console.error(error);
    }
}

async function removeFromCart(bookId) {
    const token = getToken();
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/cart/items/${Number(bookId)}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` }
        });
        if (res.status === 401) {
            clearExpiredSession();
            window.location.href = "login-register.html?v=13";
            return;
        }
        if (!res.ok) {
            const data = await readJsonResponse(res);
            showToast(data.error || "Could not remove this book.", "error");
            return;
        }
        await loadCart();
        showToast("Book removed from your cart.");
    } catch (error) {
        showToast("Cannot connect to the bookstore service.", "error");
        console.error(error);
    }
}

window.addToCart = addToCart;
window.loadCart = loadCart;
window.showToast = showToast;
document.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".right-aside")?.addEventListener("click", event => {
        const button = event.target.closest("[data-remove-book]");
        if (button) removeFromCart(button.dataset.removeBook);
    });
    loadCart();
});
window.addEventListener("pageshow", loadCart);
