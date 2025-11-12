# Architecture (MVP)

## Context
HR uploads resume → system parses and extracts → AI agent drafts PAN/Aadhaar request → candidate docs stored and viewable.

## Components
- Frontend (React): upload, dashboard, profile (confidences), request button, documents section.
- Backend (Django + DRF): file ingest, extraction pipeline, agent generator, doc storage, audit.
- DB (Postgres): candidates, resumes, extractions, document_requests, documents, audit_logs.
- Queue (Celery + Redis): async parse; optional async agent generation.
- LLM: structured extraction + request copy.

## Flow — Upload → Parse
sequenceDiagram
  participant FE as Frontend
  participant API as Backend API
  participant Q as Celery/Queue
  participant DB as Postgres
  participant LLM as LLM

  FE->>API: POST /candidates/upload (resume file)
  API->>DB: create Candidate, Resume, Extraction(status=queued)
  API->>Q: enqueue parse(job_id)
  FE-->>FE: show "Parsing…" status
  Q->>API: extract text (pdf/docx), regex (email/phone/PAN/Aadhaar format)
  Q->>LLM: structured resume extraction (name, email, phone, company, designation, skills[], confidence)
  Q->>DB: save extracted_json, confidence_json (status=done)
  FE->>API: GET /candidates/:id → show profile

## Flow — Request Docs (logged only)
sequenceDiagram
  FE->>API: POST /candidates/:id/request-documents
  API->>LLM: generate message (channel/email or sms) with tone/policy blurb
  API->>DB: log DocumentRequest(payload_json)
  API-->>FE: return generated copy for UI preview

## PII Hygiene
- Mask PAN/Aadhaar in UI; full value never shown by default.
- Signed URLs for document downloads; short TTL.
- Audit every view/download.
