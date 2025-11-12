# Security & PII
- Mask PAN/Aadhaar on UI; never return full numbers in list endpoints.
- Store docs behind signed URLs (short TTL).
- Log every view/download (audit_logs).
- Keep LLM prompts free of full document images; send only extracted text & non-sensitive metadata.
