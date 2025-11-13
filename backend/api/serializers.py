from rest_framework import serializers
from .models import Candidate, Extraction

class CandidateListSerializer(serializers.ModelSerializer):
    extraction_status = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = ("id", "name", "email", "company", "extraction_status", "updated_at")

    def get_extraction_status(self, obj):
        last = obj.extractions.order_by("-created_at").first()
        return last.status if last else "unknown"
