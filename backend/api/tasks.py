# """
# tasks.py
# Celery tasks for background work.
# - parse_resume_task: end-to-end resume parsing pipeline
# """

# import logging
# import time
# from celery import shared_task
# from django.db import transaction
# from django.utils import timezone

# from .models import Candidate, Extraction
# from .parsing import extract_text, deterministic_extract, llm_extract, merge_results, update_candidate
# from .utils_text import truncate

# log = logging.getLogger(__name__)

# @shared_task(
#     name="parse_resume_task",
#     autoretry_for=(Exception,),
#     retry_backoff=True,
#     retry_jitter=True,
#     max_retries=3,
# )
# def parse_resume_task(candidate_id: str, file_path: str):
#     """
#     Parse the resume and update the latest Extraction + Candidate.

#     Pipeline:
#       1) text = extract_text(path)
#       2) rule = deterministic_extract(text)
#       3) llm = llm_extract(text, hints=rule)  # if configured; else empty
#       4) extracted, confidence = merge_results(rule, llm)
#       5) Save Extraction (raw_text truncated) and update Candidate
#     """
#     t0 = time.time()
#     log.info("parse_start candidate_id=%s path=%s", candidate_id, file_path)

#     try:
#         text = extract_text(file_path)
#         if not text or len(text) < 20:
#             raise ValueError("No extractable text (encrypted or image-only PDF?)")

#         rule = deterministic_extract(text)
#         llm = llm_extract(text, hints=rule)  # returns empty Extracted() if provider/key missing
#         extracted, confidence = merge_results(rule, llm)

#         with transaction.atomic():
#             cand = Candidate.objects.select_for_update().get(id=candidate_id)
#             last = cand.extractions.order_by("-created_at").first()
#             if not last:
#                 last = Extraction.objects.create(candidate=cand, status="queued")

#             last.raw_text = truncate(text, 5000)
#             last.extracted_json = extracted.model_dump()
#             last.confidence_json = confidence
#             last.status = "done"
#             last.error_message = ""
#             last.save()

#             update_candidate(cand, extracted)

#         log.info(
#             "parse_done candidate_id=%s dt_ms=%d email=%s phone=%s skills=%d",
#             candidate_id, int(1000 * (time.time() - t0)),
#             extracted.email, extracted.phone, len(extracted.skills or []),
#         )
#         return {"candidate_id": candidate_id, "parsed": True}

#     except Exception as e:
#         # Mark extraction as error but don't kill the whole queue
#         with transaction.atomic():
#             try:
#                 cand = Candidate.objects.select_for_update().get(id=candidate_id)
#                 last = cand.extractions.order_by("-created_at").first()
#                 if last:
#                     last.status = "error"
#                     last.error_message = str(e)[:800]
#                     last.save(update_fields=["status", "error_message", "updated_at"])
#             except Exception:
#                 pass
#         log.exception("parse_error candidate_id=%s err=%s", candidate_id, e)
#         raise


import time
from celery import shared_task
from django.db import transaction
from .models import Candidate, Extraction
from .parsing import extract_text, deterministic_extract, llm_extract, merge_results, update_candidate

@shared_task(name="parse_resume_task")
def parse_resume_task(candidate_id: str, file_path: str):
    try:
        text = extract_text(file_path)
        rule = deterministic_extract(text)
        llm = llm_extract(text, rule)  # empty Extracted() if LLM not configured
        extracted, conf = merge_results(rule, llm)

        with transaction.atomic():
            cand = Candidate.objects.select_for_update().get(id=candidate_id)
            last = cand.extractions.order_by("-created_at").first()
            if not last:
                last = Extraction.objects.create(candidate=cand, status="queued")

            last.raw_text = text[:10000]
            last.extracted_json = extracted.model_dump()
            last.confidence_json = conf
            last.status = "done"
            last.save()

            update_candidate(cand, extracted)

        return {"candidate_id": candidate_id, "status": "done"}

    except Exception as e:
        with transaction.atomic():
            cand = Candidate.objects.get(id=candidate_id)
            last = cand.extractions.order_by("-created_at").first()
            if not last:
                last = Extraction.objects.create(candidate=cand, status="queued")
            last.status = "error"
            last.error_message = str(e)
            last.save()
        return {"candidate_id": candidate_id, "status": "error", "error": str(e)}
