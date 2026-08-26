/**
 * FloodShield API Client
 * Connects frontend to Render backend
 */

const BASE_URL =
  import.meta.env.VITE_API_URL || "https://floodshield-backend.onrender.com";

const headers = (token) => ({
  "Content-Type": "application/json",
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});

async function req(method, path, body, token) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: headers(token),
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.detail || `API error ${res.status}`);
  return json;
}

/** Auth */
export const loginUser = (email, password) =>
  req("POST", "/api/auth/login", { email, password });

export const registerUser = (email, password, full_name) =>
  req("POST", "/api/auth/register", { email, password, full_name, role: "business_owner" });

/** Business */
export const createBusiness = (data, token) =>
  req("POST", "/api/businesses", data, token);

export const getBusinesses = (token) =>
  req("GET", "/api/businesses", null, token);

/** Inventory */
export const getInventory = (businessId, token) =>
  req("GET", `/api/businesses/${businessId}/inventory`, null, token);

export const addInventoryItem = (businessId, item, token) =>
  req("POST", `/api/businesses/${businessId}/inventory`, item, token);

/** Risk */
export const getRisk = (businessId, token) =>
  req("GET", `/api/risk/business/${businessId}`, null, token);

/** Warehouse recommendation */
export const getWarehouseRec = (businessId, token) =>
  req("GET", `/api/warehouses/recommend/${businessId}`, null, token);

/** Vehicle match */
export const getVehicleMatch = (businessId, token) =>
  req("GET", `/api/vehicles/match/${businessId}`, null, token);

/** Map API inventory item → frontend item shape */
export function mapApiItem(item) {
  return {
    id: item.id,
    name: item.item_name,
    category: item.category || "General",
    quantity: Math.round((item.quantity || 0) * 100),
    value: item.total_value || item.unit_value || 0,
    location: "Registered Location",
    priority: item.evacuation_priority ? item.evacuation_priority * 10 : 60,
    risk: (item.evacuation_priority || 0) >= 8 ? "High" : "Medium",
    _apiId: item.id,
  };
}

/** Map frontend form → API body */
export function mapFormToApi(form) {
  const qty = Number(form.quantity) || 1;
  const val = Number(form.value) || 0;
  return {
    item_name: form.name,
    category: form.category,
    quantity: qty / 100,
    unit: "units",
    unit_value: val,
    total_value: val,
    evacuation_priority: form.location === "Riverside Depot" ? 9 : 6,
  };
}
