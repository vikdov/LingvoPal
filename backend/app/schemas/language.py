# backend/app/schemas/language.py
"""Language reference data (read-only)"""

from pydantic import BaseModel, Field, ConfigDict


class LanguageResponse(BaseModel):
    """Language reference data"""

    id: int
    code: str = Field(..., description="ISO 639-1 code (e.g., 'en', 'pl', 'es')")
    name: str = Field(..., description="Human-readable name (e.g., 'English')")

    model_config = ConfigDict(from_attributes=True)


__all__ = ["LanguageResponse"]
