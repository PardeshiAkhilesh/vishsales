// ─── API CONFIGURATION ───────────────────────────────────────────
const API_BASE_URL = "http://localhost:8000/api";

// Helper: get token from localStorage
const getToken = () => localStorage.getItem("vishal_token");

// Helper: set auth headers
const authHeaders = () => ({
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`
});

// ─── AUTH API ────────────────────────────────────────────────────
const authAPI = {
    register: async (name, email, password, phone = "") => {
        const res = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password, phone })
        });
        return res.json();
    },

    login: async (email, password) => {
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        return res.json();
    },

    getProfile: async () => {
        const res = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: authHeaders()
        });
        return res.json();
    },

    logout: () => {
        localStorage.removeItem("vishal_token");
        localStorage.removeItem("vishal_user");
        window.location.href = "login.html";
    }
};

// ─── PRODUCTS API ────────────────────────────────────────────────
const productsAPI = {
    getAll: async (category = "", brand = "") => {
        let url = `${API_BASE_URL}/products?limit=100`;
        if (category) url += `&category=${category}`;
        if (brand) url += `&brand=${brand}`;
        const res = await fetch(url);
        return res.json();
    },

    getById: async (id) => {
        const res = await fetch(`${API_BASE_URL}/products/${id}`);
        return res.json();
    },

    search: async (query) => {
        const res = await fetch(`${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`);
        return res.json();
    },

    getByCategory: async (category) => {
        const res = await fetch(`${API_BASE_URL}/products/category/${category}`);
        return res.json();
    }
};

// ─── CART API ────────────────────────────────────────────────────
const cartAPI = {
    getCart: async () => {
        const res = await fetch(`${API_BASE_URL}/cart`, {
            headers: authHeaders()
        });
        return res.json();
    },

    addItem: async (productId, productName, price, quantity, image) => {
        const res = await fetch(`${API_BASE_URL}/cart`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ product_id: productId, product_name: productName, 
                                   price, quantity, image })
        });
        return res.json();
    },

    removeItem: async (itemId) => {
        const res = await fetch(`${API_BASE_URL}/cart/${itemId}`, {
            method: "DELETE",
            headers: authHeaders()
        });
        return res.json();
    },

    clearCart: async () => {
        const res = await fetch(`${API_BASE_URL}/cart`, {
            method: "DELETE",
            headers: authHeaders()
        });
        return res.json();
    }
};

// ─── CONTACT API ─────────────────────────────────────────────────
const contactAPI = {
    submit: async (name, email, message, phone = "") => {
        const res = await fetch(`${API_BASE_URL}/contact`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, message, phone })
        });
        return res.json();
    }
};

// ─── EXCHANGE API ────────────────────────────────────────────────
const exchangeAPI = {
    submit: async (data) => {
        const res = await fetch(`${API_BASE_URL}/exchange`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        return res.json();
    }
};

// ─── CHATBOT API ─────────────────────────────────────────────────
const chatbotAPI = {
    send: async (message) => {
        const res = await fetch(`${API_BASE_URL}/chatbot`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });
        return res.json();
    }
};

// ─── UTILITY: Check Login State ──────────────────────────────────
const isLoggedIn = () => !!getToken();

const requireLogin = () => {
    if (!isLoggedIn()) {
        alert("Please login to continue");
        window.location.href = "login.html";
        return false;
    }
    return true;
};

// Update nav based on auth state
const updateNav = () => {
    const user = JSON.parse(localStorage.getItem("vishal_user") || "{}");
    const loginBtn = document.getElementById("loginBtn");
    const userMenu = document.getElementById("userMenu");
    const userName = document.getElementById("userName");

    if (isLoggedIn() && user.name) {
        if (loginBtn) loginBtn.style.display = "none";
        if (userMenu) userMenu.style.display = "block";
        if (userName) userName.textContent = `Hi, ${user.name}`;
    } else {
        if (loginBtn) loginBtn.style.display = "block";
        if (userMenu) userMenu.style.display = "none";
    }
};

document.addEventListener("DOMContentLoaded", updateNav);
