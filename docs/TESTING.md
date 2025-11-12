# Test Plan
- Unit: parsers (pdf/docx), regex extractors (email/phone/PAN/Aadhaar), merger logic.
- API: upload → status transitions; request-documents returns logged copy; submit-documents stores files.
- UI: happy path e2e (Cypress/Playwright) for upload → profile → request → upload docs.
- Non-functional: max resume 5MB, timeouts, rate limit on upload and request routes.
