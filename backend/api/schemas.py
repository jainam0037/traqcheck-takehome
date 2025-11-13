# """
# schemas.py
# Pydantic models for structured extraction + confidence.
# Keeps our contract explicit and validates/normalizes at the edge.
# """

# from typing import List, Optional, Dict
# from pydantic import BaseModel, Field, field_validator
# from .utils_text import normalize_space, canonical_phone

# class Extracted(BaseModel):
#     name: str = ""
#     email: str = ""
#     phone: str = ""
#     company: str = ""
#     designation: str = ""
#     skills: List[str] = Field(default_factory=list)

#     @field_validator("name", "email", "company", "designation")
#     @classmethod
#     def _norm(cls, v: str) -> str:
#         return normalize_space(v or "")

#     @field_validator("phone")
#     @classmethod
#     def _norm_phone(cls, v: str) -> str:
#         return canonical_phone(v or "")

#     @field_validator("skills")
#     @classmethod
#     def _norm_skills(cls, v: List[str]) -> List[str]:
#         seen = set()
#         out: List[str] = []
#         for item in v or []:
#             k = normalize_space(item).lower()
#             if k and k not in seen:
#                 seen.add(k)
#                 out.append(item.strip())
#         return out[:20]  # cap

# class Confidence(BaseModel):
#     name: float = 0.0
#     email: float = 0.0
#     phone: float = 0.0
#     company: float = 0.0
#     designation: float = 0.0
#     skills: float = 0.0

#     def to_dict(self) -> Dict[str, float]:
#         return self.model_dump()


from typing import List, Dict
from pydantic import BaseModel, Field

class Extracted(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    designation: str = ""
    skills: List[str] = Field(default_factory=list)

class Confidence(BaseModel):
    name: float = 0.0
    email: float = 0.0
    phone: float = 0.0
    company: float = 0.0
    designation: float = 0.0
    skills: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return self.model_dump()
