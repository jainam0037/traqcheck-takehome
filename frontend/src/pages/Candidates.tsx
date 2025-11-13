import React, { useEffect, useState } from "react";
import { listCandidates } from "../api/client";
import type { CandidateRow } from "../types";

export default function Candidates() {
  const [rows, setRows] = useState<CandidateRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await listCandidates() as CandidateRow[];
        setRows(data);
      } catch (e: any) {
        setErr(e.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="p-6">Loading…</div>;
  if (err) return <div className="p-6 text-red-600">{err}</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Candidates</h1>
      {rows.length === 0 ? (
        <div className="text-gray-600">No candidates yet.</div>
      ) : (
        <div className="overflow-x-auto border rounded">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="p-3">Name</th>
                <th className="p-3">Email</th>
                <th className="p-3">Company</th>
                <th className="p-3">Status</th>
                <th className="p-3">Updated</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.id} className="border-t">
                  <td className="p-3">
                    <a className="text-blue-600 underline" href={`/candidates/${r.id}`}>
                      {r.name || "—"}
                    </a>
                  </td>
                  <td className="p-3">{r.email || "—"}</td>
                  <td className="p-3">{r.company || "—"}</td>
                  <td className="p-3">{r.extraction_status}</td>
                  <td className="p-3">{new Date(r.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
