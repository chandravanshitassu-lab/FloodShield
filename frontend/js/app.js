const API_URL = "http://127.0.0.1:8000";

const analyzeBtn = document.getElementById("analyzeBtn");
const riskLevel = document.getElementById("riskLevel");
const tableBody = document.getElementById("inventoryTable");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const summary = document.getElementById("summary");
const totalProducts = document.getElementById("totalProducts");
const criticalCount = document.getElementById("criticalCount");
const highCount = document.getElementById("highCount");
const inventoryValue = document.getElementById("inventoryValue");
const riskBadge = document.getElementById("riskBadge");
const backendStatus = document.getElementById("backendStatus");
const backendStatusWrap = document.getElementById("backendStatusWrap");


analyzeBtn.addEventListener("click", analyzeInventory);
riskLevel.addEventListener("change", updateRiskSelectorStyle);

updateRiskSelectorStyle();
checkBackendStatus();


function updateRiskSelectorStyle() {
    riskLevel.classList.remove("risk-low", "risk-medium", "risk-high");
    riskLevel.classList.add(`risk-${riskLevel.value}`);
}


function setBackendStatus(connected) {
    if (!backendStatus) {
        return;
    }

    if (connected) {
        backendStatus.textContent = "Backend Connected";
        backendStatus.classList.remove("offline");
        if (backendStatusWrap) {
            backendStatusWrap.classList.remove("offline");
        }
        return;
    }

    backendStatus.textContent = "Backend Unavailable";
    backendStatus.classList.add("offline");
    if (backendStatusWrap) {
        backendStatusWrap.classList.add("offline");
    }
}


async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_URL}/health`);
        setBackendStatus(response.ok);
    } catch (error) {
        setBackendStatus(false);
    }
}


function parseErrorDetail(payload) {
    if (!payload) {
        return "";
    }

    if (typeof payload.detail === "string") {
        return payload.detail;
    }

    if (Array.isArray(payload.detail)) {
        return payload.detail
            .map((item) => item.msg || JSON.stringify(item))
            .join("; ");
    }

    if (payload.message) {
        return String(payload.message);
    }

    return "";
}


function friendlyHttpError(status, detail) {
    const lowered = (detail || "").toLowerCase();

    if (status === 400 || status === 422) {
        if (lowered.includes("flood risk")) {
            return detail || "Invalid flood risk.";
        }
        if (lowered.includes("inventory")) {
            return detail || "Invalid inventory data.";
        }
        return detail || "Server validation error.";
    }

    if (status >= 500) {
        return detail || "Unable to analyze inventory.";
    }

    return detail || `Unable to analyze inventory (HTTP ${status}).`;
}


async function analyzeInventory() {
    const risk = riskLevel.value;

    tableBody.innerHTML = "";
    errorBox.classList.add("hidden");
    errorBox.innerText = "";
    summary.classList.add("hidden");
    loading.classList.remove("hidden");
    analyzeBtn.disabled = true;
    analyzeBtn.innerText = "Analyzing...";

    try {
        const response = await fetch(
            `${API_URL}/inventory/prioritize?flood_risk_level=${encodeURIComponent(risk)}`,
            {
                method: "POST",
                headers: {
                    "accept": "application/json"
                }
            }
        );

        if (!response.ok) {
            let detail = "";
            try {
                const errorPayload = await response.json();
                detail = parseErrorDetail(errorPayload);
            } catch (parseError) {
                detail = "";
            }
            throw new Error(friendlyHttpError(response.status, detail));
        }

        const data = await response.json();

        if (!data || !Array.isArray(data.products)) {
            throw new Error("Unable to analyze inventory.");
        }

        displayResults(data);
        setBackendStatus(true);

    } catch (error) {
        console.error(error);

        const message = error && error.message
            ? String(error.message)
            : "";

        const isNetworkError =
            error instanceof TypeError
            || message.toLowerCase().includes("failed to fetch")
            || message.toLowerCase().includes("networkerror");

        if (isNetworkError) {
            errorBox.innerText =
                "Backend unavailable. Make sure FastAPI is running on port 8000.";
            setBackendStatus(false);
        } else {
            errorBox.innerText = message || "Unable to analyze inventory.";
        }

        errorBox.classList.remove("hidden");
        riskBadge.innerText = "NO RESULT";
        riskBadge.className = "risk-badge";

    } finally {
        loading.classList.add("hidden");
        analyzeBtn.disabled = false;
        analyzeBtn.innerText = "Analyze Inventory";
    }
}


function displayResults(data) {
    const products = data.products || [];
    const floodRisk = String(
        data.flood_risk_level || riskLevel.value
    ).toLowerCase();

    summary.classList.remove("hidden");
    totalProducts.innerText = products.length;

    criticalCount.innerText = products.filter(
        (item) => item.priority_level === "Critical"
    ).length;

    highCount.innerText = products.filter(
        (item) => item.priority_level === "High"
    ).length;

    const totalValue = products.reduce(
        (sum, item) => sum + Number(item.inventory_value || 0),
        0
    );

    inventoryValue.innerText =
        "$" + totalValue.toLocaleString("en-US", {
            minimumFractionDigits: 2
        });

    riskBadge.innerText = `${floodRisk.toUpperCase()} RISK`;
    riskBadge.className = `risk-badge ${floodRisk}`;

    products.forEach((product) => {
        const row = document.createElement("tr");
        const priorityClass = String(
            product.priority_level || "low"
        ).toLowerCase();
        const actionText = product.recommended_action || "MONITOR";
        const actionClass = String(actionText)
            .toLowerCase()
            .replace(/\s+/g, "-");

        row.innerHTML = `
            <td>
                <span class="priority ${priorityClass}">
                    ${escapeHTML(product.priority_level)}
                </span>
            </td>
            <td>
                <strong>${escapeHTML(product.name)}</strong>
            </td>
            <td>${escapeHTML(product.category)}</td>
            <td>${product.stock_quantity}</td>
            <td>
                $${Number(product.inventory_value).toLocaleString("en-US", {
                    minimumFractionDigits: 2
                })}
            </td>
            <td>${product.vulnerability_score}%</td>
            <td>
                <span class="score">${product.priority_score}</span>
            </td>
            <td>
                <span class="action ${actionClass}">
                    ${escapeHTML(actionText)}
                </span>
            </td>
        `;

        tableBody.appendChild(row);
    });
}


function escapeHTML(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
}
