// Central place for API response/DTO types so components stay clean.

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


export type CandidateDetail = {
id: string;
extracted: Partial<Extracted>;
confidence: Partial<Confidence>;
documents: { id: string; type: "PAN" | "AADHAAR"; filename: string; uploaded_at: string; verified?: boolean }[];
requests: { id: string; channel: "email" | "sms"; created_at: string; preview?: any }[];
extraction_status: "queued" | "done" | "error" | string;
};


export type RequestDocumentsBody = {
channel?: "email" | "sms";
upload_url: string;
org_name?: string;
support_email?: string;
};


export type RequestDocumentsResponse = {
id: string; // DocumentRequest id
preview: { subject: string; email_body: string; sms_body: string };
};


export type SubmitDocumentsResponse = {
saved: { id: string; type: "PAN" | "AADHAAR"; filename: string }[];
};