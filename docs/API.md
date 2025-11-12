# API Contracts (MVP)

## POST /candidates/upload  (multipart/form-data)
file: resume (pdf|docx)
→ 201
{ "id": "uuid", "status": "parsing" }

## GET /candidates
→ 200
[ { "id":"uuid","name":"...","email":"...","company":"...","extraction_status":"done|queued|error","updated_at":"..." } ]

## GET /candidates/:id
→ 200
{
  "id":"uuid",
  "extracted": {
    "name":"...", "email":"...", "phone":"+1...", "company":"...",
    "designation":"...", "skills":["React","Django", "..."]
  },
  "confidence": { "name":0.92, "email":0.99, "phone":0.96, "company":0.85, "designation":0.8, "skills":0.75 },
  "documents":[
    {"type":"PAN","url":"<signed-url>","uploaded_at":"..."},
    {"type":"AADHAAR","url":"<signed-url>","uploaded_at":"..."}
  ],
  "requests":[
    {"id":"uuid","channel":"email","created_at":"...","preview":{"subject":"...","body":"..."}}]
}

## POST /candidates/:id/request-documents
body: { "preferred_channel":"email|sms" }  // optional
→ 201
{
  "channel":"email",
  "generated":{
    "subject":"Action Needed: PAN & Aadhaar for Background Verification",
    "body":"Hi <Name>, ...",
    "data_policy_blurb":"We store documents securely..."
  },
  "logged_request_id":"uuid"
}

## POST /candidates/:id/submit-documents  (multipart/form-data)
pan_image?: file, aadhaar_image?: file
→ 201
{ "stored": true, "uploaded": ["PAN","AADHAAR"] }
