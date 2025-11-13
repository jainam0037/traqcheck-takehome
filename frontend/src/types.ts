// Central place for API response/DTO types so components stay clean.

export type ExtractionStatus = "queued" | "parsing" | "done" | "error" | string;
export type DocType = "PAN" | "AADHAAR";
export type Channel = "email" | "sms";

// Row used by /candidates list endpoint
export type CandidateRow = {
  id: string;
  name: string;
  email: string;
  company: string;
  extraction_status: "queued" | "done" | "error" | string;
  updated_at: string;
};

export type Confidence = Record<
  "name" | "email" | "phone" | "company" | "designation" | "skills",
  number
>;

export type Extracted = {
  name: string;
  email: string;
  phone: string;
  company: string;
  designation: string;
  skills: string[];
};

export type CandidateDocument = {
  id: string;
  type: DocType;
  filename: string;
  uploaded_at: string;
  verified?: boolean;
};

export type DocumentRequest = {
  id: string;
  channel: "email" | "sms";
  created_at: string;
  preview?: DocumentRequestPreview; // <- concrete type
};

export type DocumentRequestPreview = {
  subject: string;
  email_body: string;
  sms_body: string;
  sent?: boolean;
  sent_at?: string;   // ISO timestamp
  error?: string;     // delivery error, if any
};

export type CandidateRequest = {
  id: string;
  channel: Channel;
  created_at: string;
  // LLM payload preview; keep tolerant to schema changes
  preview?: DocumentRequestPreview | unknown;
};

// export type CandidateDetail = {
//   id: string;
//   extracted: Partial<Extracted>;
//   confidence: Partial<Confidence>;
//   documents: CandidateDocument[];
//   requests: CandidateRequest[];
//   extraction_status: ExtractionStatus;
// };

export type CandidateDetail = {
  id: string;
  extracted: Partial<Extracted>;
  confidence: Partial<Confidence>;
  documents: {
    id: string;
    type: "PAN" | "AADHAAR";
    filename: string;
    uploaded_at: string;
    verified?: boolean;
  }[];
  requests: {
    id: string;
    channel: "email" | "sms";
    created_at: string;
    preview?: DocumentRequestPreview; // typed preview (was any)
  }[];
  extraction_status: "queued" | "done" | "error" | string;
};

// Returned by POST /candidates/upload
export type UploadResumeResponse = {
  id: string;
  status: ExtractionStatus;
};

export type RequestDocumentsBody = {
  channel?: Channel;
  upload_url: string;
  org_name?: string;
  support_email?: string;
  send_now?: boolean; 
};

export type RequestDocumentsResponse = {
  id: string; // DocumentRequest id
  preview: DocumentRequestPreview;
};

export type SubmitDocumentsResponse = {
  saved: { id: string; type: "PAN" | "AADHAAR"; filename: string }[];
};
