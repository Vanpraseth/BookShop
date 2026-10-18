function getToken() {
    return localStorage.getItem("token");
}

function escapeCheckoutText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function checkoutInitials(title) {
    return String(title).split(/\s+/).slice(0, 2).map(word => word[0]).join("").toUpperCase();
}

async function readJsonResponse(res) {
    const text = await res.text();
    try {
        return text ? JSON.parse(text) : {};
    } catch (error) {
        return { error: text || "Invalid server response" };
    }
}

function setCheckoutMessage(text, type = "") {
    const message = document.getElementById("checkout-message");
    message.textContent = text;
    message.className = type;
}

function expireSession() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "login-register.html?v=13";
}

async function loadCheckoutCart() {
    const token = getToken();
    if (!token) {
        window.location.href = "login-register.html?v=13";
        return;
    }

    try {
        await loadAppConfig();
        const res = await fetch(`${API_BASE}/cart`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        const data = await readJsonResponse(res);

        if (res.status === 401) return expireSession();
        if (!res.ok) {
            document.getElementById("checkout-cart").innerHTML = `<p>${escapeCheckoutText(data.error || "Unable to load your bag.")}</p>`;
            return;
        }
        renderCheckoutCart(data);
    } catch (error) {
        document.getElementById("checkout-cart").innerHTML = `<p>The bookstore service is unavailable. Please try again.</p>`;
        console.error(error);
    }
}

function renderCheckoutCart(cart) {
    const cartBox = document.getElementById("checkout-cart");
    const items = Array.isArray(cart.items) ? cart.items : [];

    if (items.length === 0) {
        cartBox.innerHTML = `
            <div class="empty-checkout">
                <p>Your cart is empty.</p>
                <a class="button button-secondary" href="index.html?v=13">Browse books</a>
            </div>`;
        document.getElementById("place-order-btn").disabled = true;
        return;
    }

    document.getElementById("place-order-btn").disabled = false;
    cartBox.innerHTML = items.map(item => `
        <div class="checkout-item">
            <div class="checkout-item-cover" aria-hidden="true">${checkoutInitials(item.title)}</div>
            <div>
                <strong>${escapeCheckoutText(item.title)}</strong>
                <p>Quantity ${Number(item.quantity)}</p>
            </div>
            <div class="checkout-item-price">
                <b>${formatMoney(item.subtotal)}</b>
                <button class="remove-button" type="button" data-remove-book="${Number(item.book_id)}">Remove</button>
            </div>
        </div>
    `).join("");

    cartBox.innerHTML += `
        <div class="checkout-total"><span>Order total</span><strong>${formatMoney(cart.total)}</strong></div>`;
}

async function placeOrder() {
    const token = getToken();
    if (!token) return expireSession();

    const addressInput = document.getElementById("delivery-address");
    const button = document.getElementById("place-order-btn");
    const deliveryAddress = addressInput.value.trim();

    if (!deliveryAddress) {
        setCheckoutMessage("Please enter a delivery address.", "error");
        addressInput.focus();
        return;
    }

    button.disabled = true;
    button.textContent = "Placing order…";
    setCheckoutMessage("");

    try {
        const res = await fetch(`${API_BASE}/orders`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ delivery_address: deliveryAddress })
        });
        const data = await readJsonResponse(res);

        if (res.status === 401) return expireSession();
        if (!res.ok) {
            setCheckoutMessage(data.error || "Checkout failed.", "error");
            return;
        }

        setCheckoutMessage(`Order #${data.order_id} placed successfully. Opening your orders…`, "success");
        window.setTimeout(() => { window.location.href = `orders.html?v=13&placed=${encodeURIComponent(data.order_id)}`; }, 1200);
    } catch (error) {
        setCheckoutMessage("Cannot connect to the bookstore service.", "error");
        console.error(error);
    } finally {
        button.disabled = false;
        button.innerHTML = `Place order <span aria-hidden="true">→</span>`;
    }
}

async function removeFromCart(bookId) {
    const token = getToken();
    if (!token) return expireSession();

    try {
        const res = await fetch(`${API_BASE}/cart/items/${Number(bookId)}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` }
        });
        if (res.status === 401) return expireSession();
        if (!res.ok) {
            const data = await readJsonResponse(res);
            setCheckoutMessage(data.error || "Could not remove this book.", "error");
            return;
        }
        await loadCheckoutCart();
    } catch (error) {
        setCheckoutMessage("Cannot connect to the bookstore service.", "error");
        console.error(error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadCheckoutCart();
    document.getElementById("place-order-btn")?.addEventListener("click", placeOrder);
    document.getElementById("checkout-cart")?.addEventListener("click", event => {
        const button = event.target.closest("[data-remove-book]");
        if (button) removeFromCart(button.dataset.removeBook);
    });
});
