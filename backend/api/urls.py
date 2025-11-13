from django.urls import path
from . import views

urlpatterns = [
    path("healthz", views.health, name="health"),
    path("candidates/upload", views.upload_resume, name="upload_resume"),
    path("candidates", views.list_candidates, name="list_candidates"),
    path("candidates/<uuid:id>", views.get_candidate, name="get_candidate"),
    path("candidates/<uuid:id>/reparse", views.reparse_candidate, name="reparse_candidate"),
    path("candidates/<uuid:id>/request-documents", views.request_documents, name="request_documents"),
    path("candidates/<uuid:id>/submit-documents", views.submit_documents, name="submit_documents"),
]
