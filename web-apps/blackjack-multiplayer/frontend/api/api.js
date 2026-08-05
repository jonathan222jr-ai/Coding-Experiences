const API_BASE = "http://127.0.0.1:5000";

async function apiPost(path, data) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return await res.json();
  } catch (err) {
    console.error("POST request failed:", err);
    return { error: "Request failed" };
  }
}

async function apiGet(path) {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    return await res.json();
  } catch (err) {
    console.error("GET request failed:", err);
    return { error: "Request failed" };
  }
}
