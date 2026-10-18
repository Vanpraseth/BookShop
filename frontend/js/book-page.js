const bookId = new URLSearchParams(window.location.search).get("id");

function initialsForBook(title) {
    const ignored = new Set(["the", "a", "an", "of", "to"]);
    return String(title).split(/\s+/)
        .filter(word => word && !ignored.has(word.toLowerCase()))
        .slice(0, 2)
        .map(word => word[0])
        .join("")
        .toUpperCase() || "CH";
}

async function loadBook(id) {
    const content = document.querySelector(".book-content");

    if (!id) {
        content.innerHTML = `<h1>Book not found</h1><p>Return to the catalogue and choose a title.</p>`;
        return;
    }

    try {
        await loadAppConfig();
        const response = await fetch(`${API_BASE}/books/${encodeURIComponent(id)}`);
        if (!response.ok) throw new Error("Book not found");
        renderBook(await response.json());
    } catch (error) {
        content.innerHTML = `
            <p class="eyebrow">UNAVAILABLE</p>
            <h1>We couldn't open this book</h1>
            <p>Please return to the catalogue and try again.</p>
            <a class="button" href="index.html?v=13">Back to catalogue</a>`;
        console.error(error);
    }
}

function renderBook(book) {
    const title = document.querySelector(".main-header h1");
    const author = document.querySelector(".main-header h2");
    const category = document.querySelector(".book-category");
    const description = document.querySelector(".description p");
    const stock = document.querySelector(".stock-price-cart h3");
    const price = document.querySelector(".stock-price-cart h2");
    const button = document.querySelector(".add-to-cart-button");
    const visual = document.querySelector(".book-visual");
    const coverTitle = document.getElementById("book-cover-title");

    document.title = `${book.title} — ${APP_CONFIG.applicationName}`;
    title.textContent = book.title;
    author.textContent = `by ${book.author}`;
    category.textContent = book.category_name;
    description.textContent = book.description || "No description is available for this book.";
    stock.textContent = Number(book.stock_quantity) > 0 ? `${book.stock_quantity} copies in stock` : "Currently unavailable";
    price.textContent = formatMoney(book.price);
    visual.dataset.category = book.category_name;
    visual.dataset.coverTheme = bookCoverTheme(book.category_name);
    coverTitle.textContent = initialsForBook(book.title);

    if (Number(book.stock_quantity) <= 0) {
        button.disabled = true;
        button.textContent = "Out of stock";
    } else {
        button.addEventListener("click", () => addToCart(book.book_id, 1));
    }
}

document.addEventListener("DOMContentLoaded", () => loadBook(bookId));
