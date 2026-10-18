let allBooks = [];
let filteredBooks = [];
let currentSort = "newest-arrivals";
let currentSearch = "";

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function bookInitials(title) {
    const ignored = new Set(["the", "a", "an", "of", "to"]);
    const words = String(title).split(/\s+/).filter(word => word && !ignored.has(word.toLowerCase()));
    return words.slice(0, 2).map(word => word[0]).join("").toUpperCase() || "CH";
}

function createBookItem(book) {
    const title = escapeHtml(book.title);
    const author = escapeHtml(book.author);
    const category = escapeHtml(book.category_name);
    const description = escapeHtml(book.description || "View this book for more information.");
    const stock = Number(book.stock_quantity);
    const lowStock = stock <= 3;
    const initials = escapeHtml(bookInitials(book.title));

    return `
        <article class="catalogue-item" data-book-id="${Number(book.book_id)}" data-category="${category}" data-cover-theme="${bookCoverTheme(book.category_name)}" tabindex="0" aria-label="View ${title}">
            <div class="catalogue-cover" aria-hidden="true">
                <span>${category}</span>
                <strong>${initials}</strong>
                <small>BOOKSHOP</small>
            </div>
            <div class="book-info">
                <span class="genre">${category}</span>
                <h3 class="title">${title}</h3>
                <p class="author">by ${author}</p>
                <p class="book-description">${description}</p>
                <div class="book-meta">
                    <span class="stock ${lowStock ? "low" : ""}">${lowStock ? `Only ${stock} left` : `${stock} in stock`}</span>
                    <span class="price">${formatMoney(book.price)}</span>
                </div>
                <button class="book-link" type="button" tabindex="-1">View book <span aria-hidden="true">→</span></button>
            </div>
        </article>
    `;
}

async function loadBooks() {
    const catalogue = document.querySelector(".catalogue");

    try {
        await loadAppConfig();
        const response = await fetch(`${API_BASE}/books`);
        if (!response.ok) throw new Error("Could not load the collection.");

        allBooks = await response.json();
        filteredBooks = allBooks;
        renderFilters();
        attachFilterEvents();
        attachSortEvents();
        attachSearchEvents();
        attachResetEvent();
        attachCatalogueEvents();
        updateFilters();
    } catch (error) {
        catalogue.innerHTML = `
            <div class="catalogue-empty">
                <h3>The shelves are unavailable</h3>
                <p>Start the BookShop backend and refresh this page.</p>
            </div>`;
        updateResultCount(0, true);
        console.error(error);
    }
}

function renderBooks() {
    const catalogue = document.querySelector(".catalogue");

    if (filteredBooks.length === 0) {
        catalogue.innerHTML = `
            <div class="catalogue-empty">
                <h3>No books found</h3>
                <p>Try another title, author, or category.</p>
            </div>`;
    } else {
        catalogue.innerHTML = filteredBooks.map(createBookItem).join("");
    }

    updateResultCount(filteredBooks.length);
}

function updateResultCount(count, unavailable = false) {
    const countElement = document.querySelector(".results-count");
    if (!countElement) return;
    countElement.textContent = unavailable ? "Collection unavailable" : `${count} ${count === 1 ? "book" : "books"} available`;
}

function extractGenres(books) {
    return [...new Set(books.map(book => book.category_name))].sort();
}

function renderFilters() {
    const filterContainer = document.querySelector(".filter");
    const genres = extractGenres(allBooks);

    filterContainer.innerHTML = `
        <h2>Category</h2>
        <label><input type="checkbox" value="all" checked><span>All books</span></label>
        ${genres.map(genre => `
            <label><input type="checkbox" value="${escapeHtml(genre)}"><span>${escapeHtml(genre)}</span></label>
        `).join("")}
    `;
}

function attachFilterEvents() {
    const checkboxes = document.querySelectorAll(".filter input[type='checkbox']");
    const allBox = document.querySelector(".filter input[value='all']");

    checkboxes.forEach(box => {
        box.addEventListener("change", () => {
            if (box.value === "all" && box.checked) {
                checkboxes.forEach(other => { if (other.value !== "all") other.checked = false; });
            } else if (box.value !== "all") {
                allBox.checked = false;
            }
            updateFilters();
        });
    });
}

function attachSortEvents() {
    document.querySelectorAll(".sort input[type='radio']").forEach(radio => {
        radio.addEventListener("change", () => {
            currentSort = radio.value;
            updateFilters();
        });
    });
}

function attachSearchEvents() {
    const searchInput = document.querySelector(".main-header input[type='search']");
    searchInput?.addEventListener("input", () => {
        currentSearch = searchInput.value.trim().toLowerCase();
        updateFilters();
    });
}

function attachResetEvent() {
    document.getElementById("reset-filters")?.addEventListener("click", () => {
        window.location.reload();
    });
}

function attachCatalogueEvents() {
    const catalogue = document.querySelector(".catalogue");
    const openSelectedBook = event => {
        const card = event.target.closest(".catalogue-item");
        if (card) openBook(card.dataset.bookId);
    };

    catalogue.addEventListener("click", openSelectedBook);
    catalogue.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openSelectedBook(event);
        }
    });
}

function updateFilters() {
    const checkedGenres = [...document.querySelectorAll(".filter input[type='checkbox']:checked")]
        .map(box => box.value)
        .filter(value => value !== "all");
    const allBox = document.querySelector(".filter input[value='all']");

    if (checkedGenres.length === 0) allBox.checked = true;

    filteredBooks = allBooks.filter(book => {
        const matchesGenre = checkedGenres.length === 0 || checkedGenres.includes(book.category_name);
        const searchable = `${book.title} ${book.author} ${book.category_name}`.toLowerCase();
        return matchesGenre && searchable.includes(currentSearch);
    });

    filteredBooks = sortBooks(filteredBooks);
    renderBooks();
}

function sortBooks(books) {
    const sorted = [...books];
    const comparators = {
        title: (a, b) => a.title.localeCompare(b.title),
        author: (a, b) => a.author.localeCompare(b.author),
        genre: (a, b) => a.category_name.localeCompare(b.category_name),
        price: (a, b) => Number(a.price) - Number(b.price),
        "newest-arrivals": (a, b) => Number(b.book_id) - Number(a.book_id)
    };
    return sorted.sort(comparators[currentSort] || comparators["newest-arrivals"]);
}

function openBook(id) {
    window.location.href = `book-page.html?id=${encodeURIComponent(id)}&v=13`;
}

document.addEventListener("DOMContentLoaded", loadBooks);
