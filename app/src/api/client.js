const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function normalizeErrorMessage(data, fallback) {
  if (!data) return fallback;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    const first = data.detail[0];
    if (first?.msg && Array.isArray(first?.loc)) {
      return `${first.loc.join(".")}: ${first.msg}`;
    }
    if (first?.msg) return first.msg;
    return JSON.stringify(data.detail);
  }
  if (typeof data.detail === "object") return JSON.stringify(data.detail);
  if (typeof data.message === "string") return data.message;
  return fallback;
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch (networkError) {
    const err = new Error("Network error: unable to reach backend");
    err.network = true;
    throw err;
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    let details = null;
    try {
      const data = await response.json();
      details = data;
      message = normalizeErrorMessage(data, message);
    } catch {
      // Keep default message when body is not JSON.
    }
    const err = new Error(message);
    err.status = response.status;
    err.details = details;
    throw err;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const apiClient = {
  get: (path, headers = {}) => request(path, { method: "GET", headers }),
  post: (path, body, headers = {}) => request(path, { method: "POST", body: JSON.stringify(body), headers }),
  baseUrl: API_BASE_URL,
};
