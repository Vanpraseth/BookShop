document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const loginMessage = document.querySelector(".login .auth-message");
    const registerMessage = document.querySelector(".register .auth-message");

    function setMessage(element, text, type = "") {
        element.textContent = text;
        element.className = `auth-message ${type}`.trim();
    }

    async function postAuth(endpoint, body) {
        const response = await fetch(`${API_BASE}/auth/${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await response.json().catch(() => ({}));
        return { response, data };
    }

    function saveSession(data) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
    }

    function destinationFor(user) {
        return user?.role === "admin" ? "admin.html?v=13" : "index.html?v=13";
    }

    loginForm?.addEventListener("submit", async event => {
        event.preventDefault();
        const [emailInput, passwordInput, submitButton] = loginForm.elements;
        submitButton.disabled = true;
        submitButton.textContent = "Signing in…";
        setMessage(loginMessage, "");

        try {
            const { response, data } = await postAuth("login", {
                email: emailInput.value.trim(),
                password: passwordInput.value
            });

            if (!response.ok || !data.token) {
                setMessage(loginMessage, data.error || "Email or password is incorrect.", "error");
                return;
            }

            saveSession(data);
            setMessage(loginMessage, data.user?.role === "admin" ? "Signed in successfully. Opening the admin dashboard…" : "Signed in successfully. Opening the catalogue…", "success");
            window.setTimeout(() => { window.location.href = destinationFor(data.user); }, 650);
        } catch (error) {
            setMessage(loginMessage, "Cannot reach the bookstore service. Make sure the backend is running.", "error");
            console.error(error);
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = `Sign in <span aria-hidden="true">→</span>`;
        }
    });

    registerForm?.addEventListener("submit", async event => {
        event.preventDefault();
        const [nameInput, emailInput, passwordInput, submitButton] = registerForm.elements;
        submitButton.disabled = true;
        submitButton.textContent = "Creating account…";
        setMessage(registerMessage, "");

        try {
            const registration = await postAuth("register", {
                full_name: nameInput.value.trim(),
                email: emailInput.value.trim(),
                password: passwordInput.value
            });

            if (!registration.response.ok) {
                setMessage(registerMessage, registration.data.error || "We couldn't create that account.", "error");
                return;
            }

            const login = await postAuth("login", {
                email: emailInput.value.trim(),
                password: passwordInput.value
            });

            if (!login.response.ok || !login.data.token) {
                setMessage(registerMessage, "Account created. Please sign in above.", "success");
                return;
            }

            saveSession(login.data);
            setMessage(registerMessage, "Your account is ready. Opening the catalogue…", "success");
            window.setTimeout(() => { window.location.href = destinationFor(login.data.user); }, 650);
        } catch (error) {
            setMessage(registerMessage, "Cannot reach the bookstore service. Make sure the backend is running.", "error");
            console.error(error);
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = `Create account <span aria-hidden="true">→</span>`;
        }
    });
});
