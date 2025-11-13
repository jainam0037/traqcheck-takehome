// Minimal fetch wrapper + API calls that match your Django endpoints.
// ---------------------------------------------------------------------------
import type {
  UploadResumeResponse,
  CandidateDetail,
  CandidateRow,
  RequestDocumentsBody,
  RequestDocumentsResponse,
  SubmitDocumentsResponse,
} from "../types";

const rawBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const API_BASE = rawBase.replace(/\/+$/, ""); // strip trailing slash

async function toJSON<T>(res: Response): Promise<T> {
  const text = await res.text();
  let data: any = undefined;
  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    // non-JSON error bodies are fine; we'll fall back to text
  }

  if (!res.ok) {
    const msg =
      (data && (data.error || data.detail || data.message)) ||
      text ||
      `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export async function uploadResume(file: File): Promise<UploadResumeResponse> {
  const fd = new FormData();
  fd.append("resume", file);
  const res = await fetch(`${API_BASE}/candidates/upload`, {
    method: "POST",
    body: fd,
  });
  return toJSON<UploadResumeResponse>(res);
}

export async function getCandidate(id: string): Promise<CandidateDetail> {
  const res = await fetch(`${API_BASE}/candidates/${id}`);
  return toJSON<CandidateDetail>(res);
}

export async function listCandidates(): Promise<CandidateRow[]> {
  const res = await fetch(`${API_BASE}/candidates`);
  return toJSON<CandidateRow[]>(res);
}

export async function requestDocuments(
  id: string,
  body: RequestDocumentsBody
): Promise<RequestDocumentsResponse> {
  const res = await fetch(`${API_BASE}/candidates/${id}/request-documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return toJSON<RequestDocumentsResponse>(res);
}

export async function submitDocuments(
  id: string,
  files: { pan?: File; aadhaar?: File }
): Promise<SubmitDocumentsResponse> {
  const fd = new FormData();
  if (files.pan) fd.append("pan", files.pan);
  if (files.aadhaar) fd.append("aadhaar", files.aadhaar);

  const res = await fetch(`${API_BASE}/candidates/${id}/submit-documents`, {
    method: "POST",
    body: fd,
  });
  return toJSON<SubmitDocumentsResponse>(res);
}

// Optional helper for your "Reparse" button later
export async function reparseCandidate(
  id: string
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/candidates/${id}/reparse`, {
    method: "POST",
  });
  return toJSON<{ status: string }>(res);
}
