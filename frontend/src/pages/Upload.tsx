// Drag & drop (or click) to upload a resume, then poll until parsing is done.
// Shows the Candidate ID and a link to open the detail page.
// ---------------------------------------------------------------------------
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { uploadResume, getCandidate } from "../api/client";
import type { CandidateDetail } from "../types";

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [status, setStatus] = useState<CandidateDetail["extraction_status"] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<CandidateDetail | null>(null);
  const [uploading, setUploading] = useState(false);

  const pollRef = useRef<ReturnType<typeof window.setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }, []);

  const onPick = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  }, []);

  const clearPoll = useCallback(() => {
    if (pollRef.current) {
      window.clearTimeout(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  async function startPoll(id: string) {
    clearPoll();

    const tick = async () => {
      try {
        const d: CandidateDetail = await getCandidate(id);
        setDetail(d);
        setStatus(d.extraction_status);

        if (d.extraction_status !== "done" && d.extraction_status !== "error") {
          pollRef.current = window.setTimeout(tick, 1500);
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
      }
    };

    void tick();
  }

  const onUpload = useCallback(async () => {
    if (!file) return;
    setError(null);
    setUploading(true);
    setCandidateId(null);
    setDetail(null);
    setStatus(null);

    try {
      const resp = await uploadResume(file); // { id, status }
      setCandidateId(resp.id);
      setStatus(resp.status as CandidateDetail["extraction_status"]);
      await startPoll(resp.id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setUploading(false);
    }
  }, [file]);

  useEffect(() => {
    return () => clearPoll();
  }, [clearPoll]);

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-semibold mb-4">Upload a resume</h1>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className="border-2 border-dashed rounded-lg p-8 text-center mb-4"
        style={{ cursor: "pointer" }}
        role="button"
        aria-label="Upload resume by dragging or clicking"
      >
        <p className="mb-2">Drag &amp; drop a PDF/DOCX here</p>
        <p className="text-sm text-gray-600">or click to choose a file</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.doc,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={onPick}
          className="mt-4 hidden"
        />
      </div>

      {file && (
        <div className="mb-4 text-sm">
          Selected: <b>{file.name}</b>
        </div>
      )}

      <button
        onClick={onUpload}
        disabled={!file || uploading}
        className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
      >
        {uploading ? "Uploading…" : "Upload & Parse"}
      </button>

      {/* Status */}
      {candidateId && (
        <div className="mt-6 space-y-2">
          <div>
            Candidate ID:{" "}
            <code className="bg-gray-100 px-1 py-0.5 rounded">{candidateId}</code>
          </div>
          <div>
            Status: <span className="font-medium">{status ?? "—"}</span>
          </div>
          <div className="text-sm text-gray-600">
            Open detail:{" "}
            <Link className="text-blue-600 underline" to={`/candidates/${candidateId}`}>
              /candidates/{candidateId}
            </Link>
          </div>
        </div>
      )}

      {/* Live extracted preview (optional for Upload page) */}
      {detail?.extracted && (
        <div className="mt-6">
          <h2 className="font-semibold mb-2">Extracted (preview)</h2>
          <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
            {JSON.stringify(detail.extracted, null, 2)}
          </pre>
        </div>
      )}

      {error && <div className="mt-4 text-red-600">{error}</div>}
    </div>
  );
}
