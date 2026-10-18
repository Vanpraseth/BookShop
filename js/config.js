const configuredApiBase = document.querySelector('meta[name="api-base"]')?.content.trim();
const API_BASE = (configuredApiBase || `${window.location.origin}/api`).replace(/\/$/, "");

const APP_CONFIG = {
    applicationName: "",
    currencyCode: "",
    shipmentStatuses: [],
    notificationPollSeconds: 0
};

const BOOK_COVER_THEMES = 4;

function bookCoverTheme(category) {
    const text = String(category || "");
    const hash = [...text].reduce(
        (total, character) => ((total * 31) + character.codePointAt(0)) >>> 0,
        0
    );
    return hash % BOOK_COVER_THEMES;
}

let appConfigPromise;

async function loadAppConfig() {
    if (!appConfigPromise) {
        appConfigPromise = fetch(`${API_BASE}/config`)
            .then(response => {
                if (!response.ok) throw new Error("Application configuration unavailable.");
                return response.json();
            })
            .then(config => {
                const applicationName = String(config.application_name || "").trim();
                const currencyCode = String(config.currency_code || "").trim().toUpperCase();
                const shipmentStatuses = Array.isArray(config.shipment_statuses)
                    ? config.shipment_statuses.filter(status => typeof status === "string" && status.trim())
                    : [];
                const notificationPollSeconds = Number(config.notification_poll_seconds);

                if (!applicationName || !/^[A-Z]{3}$/.test(currencyCode)
                    || shipmentStatuses.length === 0 || notificationPollSeconds <= 0) {
                    throw new Error("Application configuration is incomplete.");
                }

                APP_CONFIG.applicationName = applicationName;
                APP_CONFIG.currencyCode = currencyCode;
                APP_CONFIG.shipmentStatuses = shipmentStatuses;
                APP_CONFIG.notificationPollSeconds = notificationPollSeconds;
                return APP_CONFIG;
            });
    }
    return appConfigPromise;
}

function formatMoney(value) {
    if (!APP_CONFIG.currencyCode) {
        throw new Error("Application configuration must load before formatting money.");
    }
    return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: APP_CONFIG.currencyCode
    }).format(Number(value) || 0);
}
