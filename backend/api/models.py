import uuid
from django.db import models

class Candidate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, default="")
    email = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    company = models.CharField(max_length=255, blank=True, default="")
    designation = models.CharField(max_length=255, blank=True, default="")
    skills = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="resumes")
    file_path = models.TextField()          # absolute path on the mounted volume
    mime = models.CharField(max_length=100, blank=True, default="")
    sha256 = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

class Extraction(models.Model):
    STATUS = (("queued","queued"),("done","done"),("error","error"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="extractions")
    status = models.CharField(max_length=10, choices=STATUS, default="queued")
    raw_text = models.TextField(blank=True, default="")
    extracted_json = models.JSONField(default=dict, blank=True)
    confidence_json = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DocumentRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="document_requests")
    channel = models.CharField(max_length=10, choices=(("email","email"),("sms","sms")), default="email")
    payload_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="documents")
    type = models.CharField(max_length=10, choices=(("PAN","PAN"),("AADHAAR","AADHAAR")))
    file_path = models.TextField()
    verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.CharField(max_length=100, default="system")
    action = models.CharField(max_length=100)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="audit_logs", null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    ts = models.DateTimeField(auto_now_add=True)
