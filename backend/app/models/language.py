# backend/app/models/language.py
"""Language reference data"""

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Language(Base):
    """Language reference data (ISO 639-1 codes)"""

    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
        comment="ISO 639-1 language code (e.g., 'en', 'pl', 'es')",
    )
    name: Mapped[str] = mapped_column(
        nullable=False, comment="Human-readable language name"
    )

    def __repr__(self) -> str:
        return f"<Language {self.code}: {self.name}>"

    def __str__(self) -> str:
        return self.name


__all__ = ["Language"]
