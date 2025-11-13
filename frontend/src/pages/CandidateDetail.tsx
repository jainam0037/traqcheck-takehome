// import React from "react";
// import { Link, useParams } from "react-router-dom";
// import { getCandidate, requestDocuments, submitDocuments } from "../api/client";
// import type { CandidateDetail, RequestDocumentsResponse, DocumentRequestPreview } from "../types";


// // (optional) narrow at runtime too
// function isPreview(x: unknown): x is DocumentRequestPreview {
//   return !!x &&
//     typeof (x as any).subject === "string" &&
//     typeof (x as any).email_body === "string" &&
//     typeof (x as any).sms_body === "string";
// }
// function ConfidenceRow({ label, value }: { label: string; value?: number }) {
//   const pct = value != null ? Math.round(value * 100) : null;
//   return (
//     <div className="flex items-center gap-3 mb-2">
//       <div className="w-28 text-sm text-gray-600">{label}</div>
//       <div className="flex-1 bg-gray-200 h-2 rounded">
//         <div className="h-2 bg-black rounded" style={{ width: `${pct ?? 0}%` }} />
//       </div>
//       <span className="w-10 text-right text-sm">
//         {pct != null ? `${pct}%` : "—"}
//       </span>
//     </div>
//   );
// }

// export default function CandidateDetail() {
//   const { id } = useParams<{ id: string }>();

//   // page-level state
//   const [detail, setDetail] = React.useState<CandidateDetail | null>(null);
//   const [loading, setLoading] = React.useState(true);
//   const [pageErr, setPageErr] = React.useState<string | null>(null);

//   // request-documents state
//   const [requestPreview, setRequestPreview] =
//     React.useState<RequestDocumentsResponse["preview"] | null>(null);
//   const [reqBusy, setReqBusy] = React.useState(false);
//   const [reqErr, setReqErr] = React.useState<string | null>(null);

//   // upload-documents state
//   const [pan, setPan] = React.useState<File | null>(null);
//   const [aadhaar, setAadhaar] = React.useState<File | null>(null);
//   const [uploadBusy, setUploadBusy] = React.useState(false);
//   const [uploadErr, setUploadErr] = React.useState<string | null>(null);

//   async function refresh() {
//     if (!id) return;
//     setLoading(true);
//     setPageErr(null);
//     try {
//       const d = (await getCandidate(id)) as CandidateDetail;
//       setDetail(d);

//       // If the backend already logged a latest request, surface it
//       const maybe = d.requests?.[0]?.preview; // DocumentRequestPreview | undefined
//       if (isPreview(maybe)) {
//         setRequestPreview(maybe);             // <- now the type matches
//       } else {
//         setRequestPreview(null);
//       }
//     } catch (e: any) {
//       setPageErr(e.message || String(e));
//     } finally {
//       setLoading(false);
//     }
//   }

//   React.useEffect(() => {
//     refresh();
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//   }, [id]);

//   async function onRequestDocs() {
//     if (!id) return;
//     setReqBusy(true);
//     setReqErr(null);
//     try {
//       const r = await requestDocuments(id, {
//         channel: "email",
//         upload_url: `${window.location.origin}/upload/${id}`,
//         org_name: "TraqCheck",
//         support_email: "support@traqcheck.local",
//       });
//       setRequestPreview(r.preview);
//       await refresh();
//     } catch (e: any) {
//       setReqErr(e.message || String(e));
//     } finally {
//       setReqBusy(false);
//     }
//   }

//   async function onSubmitDocs() {
//     if (!id) return;
//     if (!pan && !aadhaar) return;
//     setUploadBusy(true);
//     setUploadErr(null);
//     try {
//       await submitDocuments(id, { pan: pan ?? undefined, aadhaar: aadhaar ?? undefined });
//       setPan(null);
//       setAadhaar(null);
//       await refresh();
//     } catch (e: any) {
//       setUploadErr(e.message || String(e));
//     } finally {
//       setUploadBusy(false);
//     }
//   }

//   if (loading) return <div className="p-6">Loading…</div>;
//   if (pageErr) return <div className="p-6 text-red-600">{pageErr}</div>;
//   if (!detail) return null;

//   const ex = detail.extracted || {};
//   const conf = detail.confidence || {};

//   return (
//     <div className="p-6 space-y-6">
//       <div className="mb-4 text-sm">
//         <Link to="/candidates" className="text-blue-600 underline">
//           ← Back to Candidates
//         </Link>
//       </div>

//       <div className="flex items-center justify-between">
//         <h1 className="text-2xl font-semibold">Candidate</h1>
//         <span className="text-sm px-2 py-1 rounded bg-gray-100">
//           Status: {detail.extraction_status}
//         </span>
//       </div>

//       {/* Extracted summary */}
//       <div className="grid md:grid-cols-2 gap-6">
//         <div className="border rounded p-4">
//           <h2 className="font-semibold mb-3">Profile</h2>
//           <div className="space-y-1 text-sm">
//             <div><b>Name:</b> {ex.name || "—"}</div>
//             <div><b>Email:</b> {ex.email || "—"}</div>
//             <div><b>Phone:</b> {ex.phone || "—"}</div>
//             <div><b>Company:</b> {ex.company || "—"}</div>
//             <div><b>Designation:</b> {ex.designation || "—"}</div>
//             <div><b>Skills:</b> {(ex.skills || []).join(", ") || "—"}</div>
//           </div>
//         </div>

//         <div className="border rounded p-4">
//           <h2 className="font-semibold mb-3">Confidence</h2>
//           <div className="text-sm">
//             <ConfidenceRow label="Name" value={(conf as any).name} />
//             <ConfidenceRow label="Email" value={(conf as any).email} />
//             <ConfidenceRow label="Phone" value={(conf as any).phone} />
//             <ConfidenceRow label="Company" value={(conf as any).company} />
//             <ConfidenceRow label="Designation" value={(conf as any).designation} />
//             <ConfidenceRow label="Skills" value={(conf as any).skills} />
//           </div>
//         </div>
//       </div>

//       {/* Document requests */}
//       <div className="border rounded p-4 space-y-3">
//         <div className="flex items-center justify-between">
//           <h2 className="font-semibold">Request PAN/Aadhaar</h2>
//           <button
//             onClick={onRequestDocs}
//             disabled={reqBusy}
//             className="px-3 py-1.5 rounded bg-black text-white disabled:opacity-50"
//           >
//             {reqBusy ? "Requesting…" : "Generate Request"}
//           </button>
//         </div>

//         {reqErr && <div className="text-red-600">{reqErr}</div>}

//         {requestPreview && (
//           <div className="bg-gray-50 p-3 rounded text-sm">
//             <div className="font-medium mb-1">Generated Email Preview</div>
//             <div className="text-gray-700 mb-1">
//               Subject: {requestPreview.subject}
//             </div>
//             <pre className="whitespace-pre-wrap">{requestPreview.email_body}</pre>
//           </div>
//         )}
//       </div>

//       {/* Uploaded documents */}
//       <div className="border rounded p-4 space-y-3">
//         <h2 className="font-semibold">Documents</h2>

//         {(detail.documents?.length ?? 0) === 0 ? (
//           <div className="text-sm text-gray-600">No documents uploaded yet.</div>
//         ) : (
//           <ul className="text-sm list-disc pl-5 space-y-1">
//             {detail.documents!.map((d) => (
//               <li key={d.id}>
//                 <b>{d.type}</b> — {d.filename} {d.verified ? "(verified)" : ""}
//                 <span className="text-gray-500">
//                   {" "}
//                   · {new Date(d.uploaded_at).toLocaleString()}
//                 </span>
//               </li>
//             ))}
//           </ul>
//         )}

//         <div className="grid md:grid-cols-2 gap-4">
//           <div>
//             <label className="block text-sm mb-1">Upload PAN</label>
//             <input
//               type="file"
//               accept="image/*,application/pdf"
//               onChange={(e) => setPan(e.target.files?.[0] ?? null)}
//             />
//           </div>
//           <div>
//             <label className="block text-sm mb-1">Upload Aadhaar</label>
//             <input
//               type="file"
//               accept="image/*,application/pdf"
//               onChange={(e) => setAadhaar(e.target.files?.[0] ?? null)}
//             />
//           </div>
//         </div>

//         <button
//           onClick={onSubmitDocs}
//           disabled={uploadBusy || (!pan && !aadhaar)}
//           className="px-3 py-1.5 rounded bg-black text-white disabled:opacity-50"
//         >
//           {uploadBusy ? "Submitting…" : "Submit Documents"}
//         </button>

//         {uploadErr && <div className="text-red-600">{uploadErr}</div>}
//       </div>
//     </div>
//   );
// }



import React from "react";
import { Link, useParams } from "react-router-dom";
import { getCandidate, requestDocuments, submitDocuments } from "../api/client";
import type {
  CandidateDetail,
  RequestDocumentsResponse,
  DocumentRequestPreview,
} from "../types";

// (optional) narrow at runtime too
function isPreview(x: unknown): x is DocumentRequestPreview {
  return (
    !!x &&
    typeof (x as any).subject === "string" &&
    typeof (x as any).email_body === "string" &&
    typeof (x as any).sms_body === "string"
  );
}

function ConfidenceRow({ label, value }: { label: string; value?: number }) {
  const pct = value != null ? Math.round(value * 100) : null;
  return (
    <div className="flex items-center gap-3 mb-2">
      <div className="w-28 text-sm text-gray-600">{label}</div>
      <div className="flex-1 bg-gray-200 h-2 rounded">
        <div className="h-2 bg-black rounded" style={{ width: `${pct ?? 0}%` }} />
      </div>
      <span className="w-10 text-right text-sm">
        {pct != null ? `${pct}%` : "—"}
      </span>
    </div>
  );
}

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();

  // page-level state
  const [detail, setDetail] = React.useState<CandidateDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [pageErr, setPageErr] = React.useState<string | null>(null);

  // request-documents state
  const [requestPreview, setRequestPreview] =
    React.useState<RequestDocumentsResponse["preview"] | null>(null);
  const [reqBusy, setReqBusy] = React.useState(false);
  const [reqErr, setReqErr] = React.useState<string | null>(null);

  // NEW: channel + sendNow UI state
  const [channel, setChannel] = React.useState<"auto" | "email" | "sms">("auto");
  const [sendNow, setSendNow] = React.useState<boolean>(false);

  // upload-documents state
  const [pan, setPan] = React.useState<File | null>(null);
  const [aadhaar, setAadhaar] = React.useState<File | null>(null);
  const [uploadBusy, setUploadBusy] = React.useState(false);
  const [uploadErr, setUploadErr] = React.useState<string | null>(null);

  async function refresh() {
    if (!id) return;
    setLoading(true);
    setPageErr(null);
    try {
      const d = (await getCandidate(id)) as CandidateDetail;
      setDetail(d);

      // If the backend already logged a latest request, surface it
      const maybe = d.requests?.[0]?.preview; // DocumentRequestPreview | undefined (may include sent/sent_at/error)
      if (isPreview(maybe)) {
        setRequestPreview(maybe);
      } else {
        setRequestPreview(null);
      }
    } catch (e: any) {
      setPageErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function onRequestDocs() {
    if (!id) return;
    setReqBusy(true);
    setReqErr(null);
    try {
      const r = await requestDocuments(id, {
        // pass channel+sendNow as requested
        channel: channel === "auto" ? undefined : channel,
        upload_url: `${window.location.origin}/upload/${id}`,
        org_name: "TraqCheck",
        support_email: "support@traqcheck.local",
        send_now: sendNow,
      });
      setRequestPreview(r.preview);
      await refresh();
    } catch (e: any) {
      setReqErr(e.message || String(e));
    } finally {
      setReqBusy(false);
    }
  }

  async function onSubmitDocs() {
    if (!id) return;
    if (!pan && !aadhaar) return;
    setUploadBusy(true);
    setUploadErr(null);
    try {
      await submitDocuments(id, { pan: pan ?? undefined, aadhaar: aadhaar ?? undefined });
      setPan(null);
      setAadhaar(null);
      await refresh();
    } catch (e: any) {
      setUploadErr(e.message || String(e));
    } finally {
      setUploadBusy(false);
    }
  }

  if (loading) return <div className="p-6">Loading…</div>;
  if (pageErr) return <div className="p-6 text-red-600">{pageErr}</div>;
  if (!detail) return null;

  const ex = detail.extracted || {};
  const conf = detail.confidence || {};

  return (
    <div className="p-6 space-y-6">
      <div className="mb-4 text-sm">
        <Link to="/candidates" className="text-blue-600 underline">
          ← Back to Candidates
        </Link>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Candidate</h1>
        <span className="text-sm px-2 py-1 rounded bg-gray-100">
          Status: {detail.extraction_status}
        </span>
      </div>

      {/* Extracted summary */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="border rounded p-4">
          <h2 className="font-semibold mb-3">Profile</h2>
          <div className="space-y-1 text-sm">
            <div><b>Name:</b> {ex.name || "—"}</div>
            <div><b>Email:</b> {ex.email || "—"}</div>
            <div><b>Phone:</b> {ex.phone || "—"}</div>
            <div><b>Company:</b> {ex.company || "—"}</div>
            <div><b>Designation:</b> {ex.designation || "—"}</div>
            <div><b>Skills:</b> {(ex.skills || []).join(", ") || "—"}</div>
          </div>
        </div>

        <div className="border rounded p-4">
          <h2 className="font-semibold mb-3">Confidence</h2>
          <div className="text-sm">
            <ConfidenceRow label="Name" value={(conf as any).name} />
            <ConfidenceRow label="Email" value={(conf as any).email} />
            <ConfidenceRow label="Phone" value={(conf as any).phone} />
            <ConfidenceRow label="Company" value={(conf as any).company} />
            <ConfidenceRow label="Designation" value={(conf as any).designation} />
            <ConfidenceRow label="Skills" value={(conf as any).skills} />
          </div>
        </div>
      </div>

      {/* Document requests */}
      <div className="border rounded p-4 space-y-3">
        <h2 className="font-semibold">Request PAN/Aadhaar</h2>

        {/* NEW: Channel + Send now controls */}
        <div className="flex items-center gap-3">
          <label className="text-sm">
            Channel:&nbsp;
            <select
              className="border rounded px-2 py-1 text-sm"
              value={channel}
              onChange={(e) => setChannel(e.target.value as "auto" | "email" | "sms")}
            >
              <option value="auto">Auto</option>
              <option value="email">Email</option>
              <option value="sms">SMS</option>
            </select>
          </label>

          <label className="text-sm flex items-center gap-2">
            <input
              type="checkbox"
              checked={sendNow}
              onChange={(e) => setSendNow(e.target.checked)}
            />
            Send now
          </label>
        </div>

        <div className="flex items-center justify-between">
          <div />
          <button
            onClick={onRequestDocs}
            disabled={reqBusy}
            className="px-3 py-1.5 rounded bg-black text-white disabled:opacity-50"
          >
            {reqBusy ? "Requesting…" : "Generate Request"}
          </button>
        </div>

        {reqErr && <div className="text-red-600">{reqErr}</div>}

        {requestPreview && (
          <div className="bg-gray-50 p-3 rounded text-sm">
            <div className="font-medium mb-1">Generated Email Preview</div>
            <div className="text-gray-700 mb-1">
              Subject: {requestPreview.subject}
            </div>
            <pre className="whitespace-pre-wrap">{requestPreview.email_body}</pre>

            {/* NEW: delivery status */}
            {requestPreview.sent && (
              <div className="text-sm text-green-700 mt-2">
                Sent{" "}
                {requestPreview.sent_at
                  ? new Date(requestPreview.sent_at).toLocaleString()
                  : "just now"}
              </div>
            )}
            {requestPreview.error && (
              <div className="text-sm text-red-600 mt-1">
                Delivery error: {requestPreview.error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Uploaded documents */}
      <div className="border rounded p-4 space-y-3">
        <h2 className="font-semibold">Documents</h2>

        {(detail.documents?.length ?? 0) === 0 ? (
          <div className="text-sm text-gray-600">No documents uploaded yet.</div>
        ) : (
          <ul className="text-sm list-disc pl-5 space-y-1">
            {detail.documents!.map((d) => (
              <li key={d.id}>
                <b>{d.type}</b> — {d.filename} {d.verified ? "(verified)" : ""}
                <span className="text-gray-500">
                  {" "}
                  · {new Date(d.uploaded_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1">Upload PAN</label>
            <input
              type="file"
              accept="image/*,application/pdf"
              onChange={(e) => setPan(e.target.files?.[0] ?? null)}
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Upload Aadhaar</label>
            <input
              type="file"
              accept="image/*,application/pdf"
              onChange={(e) => setAadhaar(e.target.files?.[0] ?? null)}
            />
          </div>
        </div>

        <button
          onClick={onSubmitDocs}
          disabled={uploadBusy || (!pan && !aadhaar)}
          className="px-3 py-1.5 rounded bg-black text-white disabled:opacity-50"
        >
          {uploadBusy ? "Submitting…" : "Submit Documents"}
        </button>

        {uploadErr && <div className="text-red-600">{uploadErr}</div>}
      </div>
    </div>
  );
}
