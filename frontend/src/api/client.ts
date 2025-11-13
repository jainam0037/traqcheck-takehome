// Minimal fetch wrapper + API calls that match your Django endpoints.
// ---------------------------------------------------------------------------
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";


async function toJSON<T>(res: Response): Promise<T> {
if (!res.ok) {
const text = await res.text();
throw new Error(text || `HTTP ${res.status}`);
}
return res.json();
}


export async function uploadResume(file: File): Promise<{ id: string; status: string }>{
const fd = new FormData();
fd.append("resume", file);
const res = await fetch(`${API_BASE}/candidates/upload`, { method: "POST", body: fd });
return toJSON(res);
}


export async function getCandidate(id: string) {
const res = await fetch(`${API_BASE}/candidates/${id}`);
return toJSON(res);
}


export async function listCandidates() {
const res = await fetch(`${API_BASE}/candidates`);
return toJSON(res);
}


export async function requestDocuments(id: string, body: import("../types").RequestDocumentsBody) {
const res = await fetch(`${API_BASE}/candidates/${id}/request-documents`, {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify(body),
});
return toJSON<import("../types").RequestDocumentsResponse>(res);
}


export async function submitDocuments(id: string, files: { pan?: File; aadhaar?: File }) {
const fd = new FormData();
if (files.pan) fd.append("pan", files.pan);
if (files.aadhaar) fd.append("aadhaar", files.aadhaar);
const res = await fetch(`${API_BASE}/candidates/${id}/submit-documents`, { method: "POST", body: fd });
return toJSON<import("../types").SubmitDocumentsResponse>(res);
}