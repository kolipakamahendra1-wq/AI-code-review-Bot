const BASE = import.meta.env.VITE_API_URL || "http://localhost:8020";

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new Error("Cannot reach the API. Is the backend running?");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? "Invalid request" : body.detail;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

const json = (body) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const getHealth = () => request("/api/health");
export const getStats = () => request("/api/stats");
export const listReviews = () => request("/api/reviews");
export const getReview = (id) => request(`/api/reviews/${id}`);
export const reviewDiff = (diff, mode) => request("/api/review/diff", json({ diff, mode }));
export const reviewPR = (url) => request("/api/review/pr", json({ url, post: false }));
