# Traqcheck Take-Home — Resume → Identity Docs (MVP)

## Goal
Upload resume → extract candidate info w/ confidences → AI-generated (logged) request for PAN/Aadhaar → accept document uploads.

## Tech (defaults)
Backend: Django + DRF, Celery, Redis, PostgreSQL
Frontend: React + Vite
LLM: OpenAI/Claude/OpenRouter via LangChain (schema-constrained)
Deploy: Railway/Render (BE+DB), Vercel (FE)

## Definition of Done
- See docs/ARCHITECTURE.md, docs/API.md, docs/SCHEMA.sql
- Security basics: masking, signed URLs, audit
- 5-min Loom: arch → upload → parse → request → upload docs
