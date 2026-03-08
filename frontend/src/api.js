// Dynamically resolve the API base URL based on the current browser hostname.
// This ensures it works whether accessed via 'localhost' or '127.0.0.1'.
const hostname = window.location.hostname;
export const API_BASE = `http://${hostname}:8001`;
export const WS_BASE = `ws://${hostname}:8001`;
