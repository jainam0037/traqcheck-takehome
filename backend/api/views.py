# """
# api/views.py
# HTTP endpoints for:
# - health check
# - resume upload & candidate listing/detail
# - reparse latest resume
# - AI-backed PAN/Aadhaar request generation
# - PAN/Aadhaar document submission

# Notes:
# - Uses settings.DOCS_DIR for all file storage (mounted volume).
# - LLM request generation uses generate_structured(); falls back to a template if not configured.
# - Sender org is always settings.ORG_NAME (or override per-request); never confuse with candidate_company.
# """

# import os
# import uuid
# import hashlib

# from django.conf import settings
# from django.shortcuts import get_object_or_404

# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, parser_classes
# from rest_framework.parsers import MultiPartParser, FormParser


# from .models import (
#     Candidate,
#     Resume,
#     Extraction,
#     DocumentRequest,
#     Document,
#     AuditLog,
# )
# from .serializers import CandidateListSerializer
# from .tasks import parse_resume_task
# from .llm_client import generate_structured  # structured JSON helper
# from core.messenger import send_email, send_sms

# # --------------------------
# # Constants
# # --------------------------
# ALLOWED_RESUME_EXTS = {".pdf", ".docx"}
# MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB

# ALLOWED_DOC_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}
# MAX_DOC_SIZE = 8 * 1024 * 1024  # 8 MB


# # --------------------------
# # Health
# # --------------------------
# @api_view(["GET"])
# def health(_req):
#     return Response({"status": "ok"})


# # --------------------------
# # Candidate listing & detail
# # --------------------------
# @api_view(["GET"])
# def list_candidates(_req):
#     qs = Candidate.objects.order_by("-updated_at").all()
#     data = CandidateListSerializer(qs, many=True).data
#     return Response(data)


# @api_view(["GET"])
# def get_candidate(_req, id):
#     cand = get_object_or_404(Candidate, pk=id)
#     last = cand.extractions.order_by("-created_at").first()

#     documents = [
#         {
#             "id": str(d.id),
#             "type": d.type,
#             "filename": os.path.basename(d.file_path),
#             "uploaded_at": d.uploaded_at,
#             "verified": d.verified,
#         }
#         for d in cand.documents.all().order_by("-uploaded_at")
#     ]

#     requests = [
#         {
#             "id": str(r.id),
#             "channel": r.channel,
#             "created_at": r.created_at,
#             "preview": r.payload_json,
#         }
#         for r in cand.document_requests.all().order_by("-created_at")
#     ]

#     return Response(
#         {
#             "id": str(cand.id),
#             "extracted": (last.extracted_json if last else {}),
#             "confidence": (last.confidence_json if last else {}),
#             "documents": documents,
#             "requests": requests,
#             "extraction_status": (last.status if last else "unknown"),
#         }
#     )


# # --------------------------
# # Upload resume → enqueue parse
# # --------------------------
# @api_view(["POST"])
# @parser_classes([MultiPartParser, FormParser])
# def upload_resume(req):
#     """
#     Multipart form with key 'resume' (.pdf | .docx).
#     Creates Candidate + Resume + Extraction(queued), saves file to DOCS_DIR/<candidate_uuid>/, and enqueues Celery parse.
#     """
#     if "resume" not in req.FILES:
#         return Response(
#             {"error": "resume file required (pdf/docx)"},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     f = req.FILES["resume"]
#     if f.size > MAX_RESUME_SIZE:
#         return Response(
#             {"error": "file too large (max 5MB)"},
#             status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
#         )

#     ext = os.path.splitext(f.name)[1].lower()
#     if ext not in ALLOWED_RESUME_EXTS:
#         return Response(
#             {"error": "unsupported file type; use .pdf or .docx"},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     # Create candidate shell; parse will backfill fields.
#     cand = Candidate.objects.create()

#     # Candidate-specific directory
#     cand_dir = os.path.join(settings.DOCS_DIR, str(cand.id))
#     os.makedirs(cand_dir, exist_ok=True)
#     fname = f"resume-{uuid.uuid4().hex}{ext}"
#     abs_path = os.path.join(cand_dir, fname)

#     # Save file + compute sha256
#     sha = hashlib.sha256()
#     with open(abs_path, "wb") as out:
#         for chunk in f.chunks():
#             out.write(chunk)
#             sha.update(chunk)

#     Resume.objects.create(
#         candidate=cand,
#         file_path=abs_path,
#         mime=f.content_type or "",
#         sha256=sha.hexdigest(),
#     )
#     Extraction.objects.create(candidate=cand, status="queued")

#     # Enqueue async parsing
#     parse_resume_task.delay(str(cand.id), abs_path)

#     return Response({"id": str(cand.id), "status": "parsing"}, status=status.HTTP_201_CREATED)


# # --------------------------
# # Reparse latest resume
# # --------------------------
# @api_view(["POST"])
# def reparse_candidate(_req, id):
#     """
#     Enqueue a fresh parse for the candidate's most recent resume.
#     Creates a new Extraction(status=queued), then schedules the task.
#     """
#     cand = get_object_or_404(Candidate, pk=id)
#     last_resume = cand.resumes.order_by("-created_at").first()
#     if not last_resume:
#         return Response({"error": "no resume found"}, status=status.HTTP_400_BAD_REQUEST)

#     Extraction.objects.create(candidate=cand, status="queued")
#     parse_resume_task.delay(str(cand.id), last_resume.file_path)

#     AuditLog.objects.create(
#         actor="system",
#         action="reparse",
#         candidate=cand,
#         metadata_json={"resume_path": last_resume.file_path},
#     )
#     return Response({"status": "queued"})


# # --------------------------
# # AI: request PAN/Aadhaar (org-safe)
# # --------------------------
# @api_view(["POST"])
# def request_documents(req, id):
#     """
#     Generate a personalized PAN/Aadhaar request and log it.
#     Body (JSON):
#       {
#         "channel": "email" | "sms",              # optional (default "email")
#         "upload_url": "https://...",             # optional; defaults to http://localhost:5173/upload/<id>
#         "org_name": "TraqCheck",                 # optional override; defaults to settings.ORG_NAME
#         "support_email": "support@..."           # optional override; defaults to settings.ORG_SUPPORT_EMAIL
#       }
#     Returns: {"id": "<DocumentRequest id>", "preview": {...}}
#     """
#     cand = get_object_or_404(Candidate, pk=id)

#     # Pull best-known extracted details; treat prior employer as candidate_company.
#     last = cand.extractions.order_by("-created_at").first()
#     extracted = last.extracted_json if last else {}
#     candidate_payload = {
#         "name": extracted.get("name") or cand.name,
#         "email": extracted.get("email") or cand.email,
#         "phone": extracted.get("phone") or cand.phone,
#         "skills": extracted.get("skills") or (cand.skills or []),
#         "candidate_company": extracted.get("company") or cand.company,
#         "designation": extracted.get("designation") or cand.designation,
#     }

#     channel = (req.data.get("channel") or "email").lower()
#     if channel not in ("email", "sms"):
#         return Response({"error": "channel must be 'email' or 'sms'"}, status=400)

#     upload_url = req.data.get("upload_url") or f"http://localhost:5173/upload/{cand.id}"
#     org_name = (req.data.get("org_name") or getattr(settings, "ORG_NAME", "TraqCheck")).strip()
#     support_email = (req.data.get("support_email") or getattr(settings, "ORG_SUPPORT_EMAIL", "support@traqcheck.local")).strip()

#     # ---- LLM prompt with explicit sender semantics ----
#     system = (
#         "You are an HR assistant writing document-collection messages on behalf of an organization.\n"
#         "You MUST treat the requesting organization as the SENDER.\n"
#         f"- The sender organization is '{org_name}'. Never imply you are the candidate's employer.\n"
#         "- 'candidate_company' (if present) is the candidate's past/current employer, NOT the sender.\n"
#         "- Write concise, professional, privacy-aware requests to collect PAN and Aadhaar.\n"
#         "- Tone: courteous, clear, formal; keep SMS <= 320 chars.\n"
#         "- Output STRICT JSON ONLY with keys: subject, email_body, sms_body. No markdown links.\n"
#     )
#     user = (
#         "Context:\n"
#         f"- Sender org: {org_name}\n"
#         f"- Support email: {support_email}\n"
#         f"- Secure upload link: {upload_url}\n"
#         f"- Candidate data: {candidate_payload}\n\n"
#         "Requirements:\n"
#         "- Subject mentions 'PAN & Aadhaar verification' or similar.\n"
#         "- Email body MUST state you are contacting on behalf of the sender org (org_name),\n"
#         "  explain purpose (onboarding/identity verification), acceptable file types (clear photo or PDF), privacy,\n"
#         "  support instructions (use support_email), and include the plain URL.\n"
#         "- SMS body must be ≤ 320 chars and include the URL.\n"
#         "- NEVER say or imply you are the candidate_company.\n"
#         "- Output EXACT JSON with keys: subject, email_body, sms_body."
#     )
#     schema = {
#         "type": "object",
#         "properties": {
#             "subject": {"type": "string"},
#             "email_body": {"type": "string"},
#             "sms_body": {"type": "string"},
#         },
#         "required": ["subject", "email_body", "sms_body"],
#         "additionalProperties": False,
#     }

#     data = generate_structured(schema, system, user) or {}

#     # ---- Fallback if LLM not configured/available ----
#     if not data:
#         sal = (candidate_payload["name"] or "there").strip()
#         data = {
#             "subject": f"{org_name} — PAN & Aadhaar verification",
#             "email_body": (
#                 f"Hi {sal},\n\n"
#                 f"To complete your background verification for onboarding with {org_name}, "
#                 "please upload clear images or PDFs of your PAN and Aadhaar using the secure link below:\n"
#                 f"{upload_url}\n\n"
#                 "We use these documents only for identity verification and do not share them. "
#                 f"If you face any issues, reply to {support_email} and we’ll help.\n\n"
#                 f"Thanks,\n{org_name} Team"
#             ),
#             "sms_body": f"{org_name}: please upload PAN & Aadhaar to complete verification: {upload_url}",
#         }

#     # ---- Final safety: sanitize any accidental sender confusion ----
#     cand_co = (candidate_payload.get("candidate_company") or "").strip()
#     if cand_co and cand_co.lower() != org_name.lower():
#         def _fix_org(text: str) -> str:
#             if not text:
#                 return text
#             # Common phrasing fixes
#             text = text.replace(f" at {cand_co}", f" at {org_name}")
#             text = text.replace(f" from {cand_co}", f" from {org_name}")
#             # Generic replacement as last resort
#             text = text.replace(cand_co, org_name)
#             return text

#         data["subject"] = _fix_org(data.get("subject", ""))
#         data["email_body"] = _fix_org(data.get("email_body", ""))
#         data["sms_body"] = _fix_org(data.get("sms_body", ""))

#     # Persist
#     dr = DocumentRequest.objects.create(candidate=cand, channel=channel, payload_json=data)
#     AuditLog.objects.create(
#         actor="agent",
#         action="request_documents",
#         candidate=cand,
#         metadata_json={"channel": channel, "request_id": str(dr.id), "org_name": org_name},
#     )
#     return Response({"id": str(dr.id), "preview": data}, status=201)


# # --------------------------
# # Upload PAN/Aadhaar files
# # --------------------------
# @api_view(["POST"])
# @parser_classes([MultiPartParser])  # multipart form-data: keys 'pan' and/or 'aadhaar'
# def submit_documents(req, id):
#     """
#     Accept uploaded PAN/Aadhaar images (either or both).
#     Allowed: .jpg/.jpeg/.png/.pdf up to 8 MB each.
#     Returns list of saved documents.
#     """
#     cand = get_object_or_404(Candidate, pk=id)
#     saved = []

#     def _save_one(field_name: str, dtype: str):
#         f = req.FILES.get(field_name)
#         if not f:
#             return

#         if f.size > MAX_DOC_SIZE:
#             raise ValueError(f"{field_name} too large (max 8MB)")

#         ext = os.path.splitext(f.name)[1].lower()
#         if ext not in ALLOWED_DOC_EXTS:
#             raise ValueError(f"{field_name} unsupported type (use jpg/jpeg/png/pdf)")

#         cand_dir = os.path.join(settings.DOCS_DIR, str(cand.id))
#         os.makedirs(cand_dir, exist_ok=True)

#         fname = f"{dtype.lower()}-{uuid.uuid4().hex}{ext}"
#         abs_path = os.path.join(cand_dir, fname)

#         with open(abs_path, "wb") as out:
#             for chunk in f.chunks():
#                 out.write(chunk)

#         d = Document.objects.create(
#             candidate=cand,
#             type=dtype,
#             file_path=abs_path,
#             verified=False,
#         )
#         saved.append({"id": str(d.id), "type": d.type, "filename": fname})

#     try:
#         _save_one("pan", "PAN")
#         _save_one("aadhaar", "AADHAAR")
#     except ValueError as e:
#         return Response({"error": str(e)}, status=400)

#     if not saved:
#         return Response({"error": "attach 'pan' and/or 'aadhaar' files"}, status=400)

#     AuditLog.objects.create(
#         actor="system",
#         action="submit_documents",
#         candidate=cand,
#         metadata_json={"saved": saved},
#     )
#     return Response({"saved": saved}, status=201)



"""
api/views.py
HTTP endpoints for:
- health check
- resume upload & candidate listing/detail
- reparse latest resume
- AI-backed PAN/Aadhaar request generation (+ optional delivery)
- PAN/Aadhaar document submission

Notes:
- Uses settings.DOCS_DIR for all file storage (mounted volume).
- LLM request generation uses generate_structured(); falls back to a template if not configured.
- Sender org is always settings.ORG_NAME (or override per-request); never confuse with candidate_company.
"""

import os
import uuid
import hashlib

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    Candidate,
    Resume,
    Extraction,
    DocumentRequest,
    Document,
    AuditLog,
)
from .serializers import CandidateListSerializer
from .tasks import parse_resume_task
from .llm_client import generate_structured  # structured JSON helper
from core.messenger import send_email, send_sms

# --------------------------
# Constants
# --------------------------
ALLOWED_RESUME_EXTS = {".pdf", ".docx"}
MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_DOC_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_DOC_SIZE = 8 * 1024 * 1024  # 8 MB


# --------------------------
# Health
# --------------------------
@api_view(["GET"])
def health(_req):
    return Response({"status": "ok"})


# --------------------------
# Candidate listing & detail
# --------------------------
@api_view(["GET"])
def list_candidates(_req):
    qs = Candidate.objects.order_by("-updated_at").all()
    data = CandidateListSerializer(qs, many=True).data
    return Response(data)


@api_view(["GET"])
def get_candidate(_req, id):
    cand = get_object_or_404(Candidate, pk=id)
    last = cand.extractions.order_by("-created_at").first()

    documents = [
        {
            "id": str(d.id),
            "type": d.type,
            "filename": os.path.basename(d.file_path),
            "uploaded_at": d.uploaded_at,
            "verified": d.verified,
        }
        for d in cand.documents.all().order_by("-uploaded_at")
    ]

    requests = [
        {
            "id": str(r.id),
            "channel": r.channel,
            "created_at": r.created_at,
            "preview": r.payload_json,
        }
        for r in cand.document_requests.all().order_by("-created_at")
    ]

    return Response(
        {
            "id": str(cand.id),
            "extracted": (last.extracted_json if last else {}),
            "confidence": (last.confidence_json if last else {}),
            "documents": documents,
            "requests": requests,
            "extraction_status": (last.status if last else "unknown"),
        }
    )


# --------------------------
# Upload resume → enqueue parse
# --------------------------
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_resume(req):
    """
    Multipart form with key 'resume' (.pdf | .docx).
    Creates Candidate + Resume + Extraction(queued), saves file to DOCS_DIR/<candidate_uuid>/, and enqueues Celery parse.
    """
    if "resume" not in req.FILES:
        return Response(
            {"error": "resume file required (pdf/docx)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    f = req.FILES["resume"]
    if f.size > MAX_RESUME_SIZE:
        return Response(
            {"error": "file too large (max 5MB)"},
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED_RESUME_EXTS:
        return Response(
            {"error": "unsupported file type; use .pdf or .docx"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create candidate shell; parse will backfill fields.
    cand = Candidate.objects.create()

    # Candidate-specific directory
    cand_dir = os.path.join(settings.DOCS_DIR, str(cand.id))
    os.makedirs(cand_dir, exist_ok=True)
    fname = f"resume-{uuid.uuid4().hex}{ext}"""
    abs_path = os.path.join(cand_dir, fname)

    # Save file + compute sha256
    sha = hashlib.sha256()
    with open(abs_path, "wb") as out:
        for chunk in f.chunks():
            out.write(chunk)
            sha.update(chunk)

    Resume.objects.create(
        candidate=cand,
        file_path=abs_path,
        mime=f.content_type or "",
        sha256=sha.hexdigest(),
    )
    Extraction.objects.create(candidate=cand, status="queued")

    # Enqueue async parsing
    parse_resume_task.delay(str(cand.id), abs_path)

    return Response({"id": str(cand.id), "status": "parsing"}, status=status.HTTP_201_CREATED)


# --------------------------
# Reparse latest resume
# --------------------------
@api_view(["POST"])
def reparse_candidate(_req, id):
    """
    Enqueue a fresh parse for the candidate's most recent resume.
    Creates a new Extraction(status=queued), then schedules the task.
    """
    cand = get_object_or_404(Candidate, pk=id)
    last_resume = cand.resumes.order_by("-created_at").first()
    if not last_resume:
        return Response({"error": "no resume found"}, status=status.HTTP_400_BAD_REQUEST)

    Extraction.objects.create(candidate=cand, status="queued")
    parse_resume_task.delay(str(cand.id), last_resume.file_path)

    AuditLog.objects.create(
        actor="system",
        action="reparse",
        candidate=cand,
        metadata_json={"resume_path": last_resume.file_path},
    )
    return Response({"status": "queued"})


# --------------------------
# Helpers for channel choice & composing preview
# --------------------------
def _choose_channel(cand, explicit_channel, extracted, confidence):
    """
    Decide 'email' | 'sms' given an optional explicit channel (can be 'auto' or None).
    Prefer email if present and reasonably confident; else SMS; else 400.
    """
    if explicit_channel in {"email", "sms"}:
        return explicit_channel
    # auto/None flow:
    email = (extracted or {}).get("email") or getattr(cand, "email", None)
    phone = (extracted or {}).get("phone") or getattr(cand, "phone", None)
    conf = confidence or {}
    email_conf = conf.get("email") or 0.0
    phone_conf = conf.get("phone") or 0.0

    # Prefer the one with >=0.5 confidence; fall back to presence.
    if email and email_conf >= 0.5:
        return "email"
    if phone and phone_conf >= 0.5:
        return "sms"
    if email:
        return "email"
    if phone:
        return "sms"

    raise ValueError("No reachable contact (email/phone) on candidate.")


def _compose_preview(candidate_payload, upload_url, org_name, support_email):
    sal = (candidate_payload.get("name") or "there").strip()
    subject = f"{org_name} — PAN & Aadhaar verification"
    email_body = (
        f"Hi {sal},\n\n"
        f"To complete your background verification for onboarding with {org_name}, "
        "please upload clear images or PDFs of your PAN and Aadhaar using the secure link below:\n"
        f"{upload_url}\n\n"
        "We use these documents only for identity verification and do not share them. "
        f"If you face any issues, reply to {support_email} and we’ll help.\n\n"
        f"Thanks,\n{org_name} Team"
    )
    sms_body = f"{org_name}: please upload PAN & Aadhaar to complete verification: {upload_url}"
    return {"subject": subject, "email_body": email_body, "sms_body": sms_body}


# --------------------------
# AI: request PAN/Aadhaar (org-safe) + optional send_now
# --------------------------
@api_view(["POST"])
def request_documents(req, id):
    """
    Generate a personalized PAN/Aadhaar request, log it, and (optionally) send now.

    Body (JSON):
      {
        "channel": "email" | "sms" | "auto" | null,   # optional; default 'auto'
        "upload_url": "https://...",                   # optional; defaults to http://localhost:5173/upload/<id>
        "org_name": "TraqCheck",                       # optional; defaults to settings.ORG_NAME
        "support_email": "support@...",                # optional; defaults to settings.ORG_SUPPORT_EMAIL
        "send_now": true | false                       # optional; default false
      }

    Returns: {"id": "<DocumentRequest id>", "preview": {...}}
    """
    cand = get_object_or_404(Candidate, pk=id)

    # Pull best-known extracted details; treat prior employer as candidate_company.
    last = cand.extractions.order_by("-created_at").first()
    extracted = last.extracted_json if last else {}
    confidence = last.confidence_json if last else {}

    candidate_payload = {
        "name": extracted.get("name") or cand.name,
        "email": extracted.get("email") or cand.email,
        "phone": extracted.get("phone") or cand.phone,
        "skills": extracted.get("skills") or (cand.skills or []),
        "candidate_company": extracted.get("company") or cand.company,
        "designation": extracted.get("designation") or cand.designation,
    }

    channel_raw = req.data.get("channel")
    channel_raw = (channel_raw or "auto").strip().lower() if isinstance(channel_raw, str) else "auto"

    upload_url = req.data.get("upload_url") or f"http://localhost:5173/upload/{cand.id}"
    org_name = (req.data.get("org_name") or getattr(settings, "ORG_NAME", "TraqCheck")).strip()
    support_email = (req.data.get("support_email") or getattr(settings, "ORG_SUPPORT_EMAIL", "support@traqcheck.local")).strip()
    send_now = bool(req.data.get("send_now", False))

    # ---- choose channel (auto/email/sms) ----
    try:
        channel = _choose_channel(cand, channel_raw if channel_raw != "auto" else None, extracted, confidence)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    # ---- LLM prompt with explicit sender semantics ----
    system = (
        "You are an HR assistant writing document-collection messages on behalf of an organization.\n"
        "You MUST treat the requesting organization as the SENDER.\n"
        f"- The sender organization is '{org_name}'. Never imply you are the candidate's employer.\n"
        "- 'candidate_company' (if present) is the candidate's past/current employer, NOT the sender.\n"
        "- Write concise, professional, privacy-aware requests to collect PAN and Aadhaar.\n"
        "- Tone: courteous, clear, formal; keep SMS <= 320 chars.\n"
        "- Output STRICT JSON ONLY with keys: subject, email_body, sms_body. No markdown links.\n"
    )
    user = (
        "Context:\n"
        f"- Sender org: {org_name}\n"
        f"- Support email: {support_email}\n"
        f"- Secure upload link: {upload_url}\n"
        f"- Candidate data: {candidate_payload}\n\n"
        "Requirements:\n"
        "- Subject mentions 'PAN & Aadhaar verification' or similar.\n"
        "- Email body MUST state you are contacting on behalf of the sender org (org_name),\n"
        "  explain purpose (onboarding/identity verification), acceptable file types (clear photo or PDF), privacy,\n"
        "  support instructions (use support_email), and include the plain URL.\n"
        "- SMS body must be ≤ 320 chars and include the URL.\n"
        "- NEVER say or imply you are the candidate_company.\n"
        "- Output EXACT JSON with keys: subject, email_body, sms_body."
    )
    schema = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "email_body": {"type": "string"},
            "sms_body": {"type": "string"},
        },
        "required": ["subject", "email_body", "sms_body"],
        "additionalProperties": False,
    }

    data = generate_structured(schema, system, user) or {}

    # ---- Fallback if LLM not configured/available ----
    if not data:
        data = _compose_preview(candidate_payload, upload_url, org_name, support_email)

    # ---- Final safety: sanitize any accidental sender confusion ----
    cand_co = (candidate_payload.get("candidate_company") or "").strip()
    if cand_co and cand_co.lower() != org_name.lower():
        def _fix_org(text: str) -> str:
            if not text:
                return text
            text = text.replace(f" at {cand_co}", f" at {org_name}")
            text = text.replace(f" from {cand_co}", f" from {org_name}")
            text = text.replace(cand_co, org_name)
            return text

        data["subject"] = _fix_org(data.get("subject", ""))
        data["email_body"] = _fix_org(data.get("email_body", ""))
        data["sms_body"] = _fix_org(data.get("sms_body", ""))

    # Persist request (as draft initially)
    dr = DocumentRequest.objects.create(candidate=cand, channel=channel, payload_json=data)
    AuditLog.objects.create(
        actor="agent",
        action="request_documents",
        candidate=cand,
        metadata_json={"channel": channel, "request_id": str(dr.id), "org_name": org_name},
    )

    # Optionally send now
    if send_now:
        ok = False
        err = None
        if channel == "email":
            to_email = (extracted or {}).get("email") or getattr(cand, "email", None)
            if not to_email:
                err = "Candidate has no email."
            else:
                ok, err = send_email(
                    to=to_email,
                    subject=data.get("subject") or "",
                    text=data.get("email_body") or "",
                )
        else:  # sms
            to_phone = (extracted or {}).get("phone") or getattr(cand, "phone", None)
            if not to_phone:
                err = "Candidate has no phone."
            else:
                ok, err = send_sms(to=to_phone, text=data.get("sms_body") or "")

        # Update the stored preview JSON with delivery info (no migration needed)
        dr.payload_json = {
            **dr.payload_json,
            "sent": bool(ok),
            "sent_at": now().isoformat(),
            **({"error": err} if err else {}),
        }
        dr.save(update_fields=["payload_json"])

    # Respond with (possibly updated) preview
    return Response({"id": str(dr.id), "preview": dr.payload_json}, status=201)


# --------------------------
# Upload PAN/Aadhaar files
# --------------------------
@api_view(["POST"])
@parser_classes([MultiPartParser])  # multipart form-data: keys 'pan' and/or 'aadhaar'
def submit_documents(req, id):
    """
    Accept uploaded PAN/Aadhaar images (either or both).
    Allowed: .jpg/.jpeg/.png/.pdf up to 8 MB each.
    Returns list of saved documents.
    """
    cand = get_object_or_404(Candidate, pk=id)
    saved = []

    def _save_one(field_name: str, dtype: str):
        f = req.FILES.get(field_name)
        if not f:
            return

        if f.size > MAX_DOC_SIZE:
            raise ValueError(f"{field_name} too large (max 8MB)")

        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED_DOC_EXTS:
            raise ValueError(f"{field_name} unsupported type (use jpg/jpeg/png/pdf)")

        cand_dir = os.path.join(settings.DOCS_DIR, str(cand.id))
        os.makedirs(cand_dir, exist_ok=True)

        fname = f"{dtype.lower()}-{uuid.uuid4().hex}{ext}"
        abs_path = os.path.join(cand_dir, fname)

        with open(abs_path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)

        d = Document.objects.create(
            candidate=cand,
            type=dtype,
            file_path=abs_path,
            verified=False,
        )
        saved.append({"id": str(d.id), "type": d.type, "filename": fname})

    try:
        _save_one("pan", "PAN")
        _save_one("aadhaar", "AADHAAR")
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    if not saved:
        return Response({"error": "attach 'pan' and/or 'aadhaar' files"}, status=400)

    AuditLog.objects.create(
        actor="system",
        action="submit_documents",
        candidate=cand,
        metadata_json={"saved": saved},
    )
    return Response({"saved": saved}, status=201)
