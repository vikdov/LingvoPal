# backend/app/repositories/specifications.py
"""
Specification pattern for reusable query filters.

Use this if you have many overlapping WHERE clauses.
Optional — only if you need it.
"""

from sqlalchemy import Select, and_

from app.models import Item, Set


class BaseSpecification:
    """Base for query specifications"""

    def apply(self, stmt: Select) -> Select:
        """Apply specification to query"""
        raise NotImplementedError


class ActiveItemsOnly(BaseSpecification):
    """Filter deleted items"""

    def apply(self, stmt: Select) -> Select:
        return stmt.where(Item.deleted_at.is_(None))


class PublicSetsOnly(BaseSpecification):
    """Filter to public (APPROVED or OFFICIAL) sets"""

    def apply(self, stmt: Select) -> Select:
        return stmt.where(Set.status.in_(["approved", "official"]))


class SetsByLanguagePair(BaseSpecification):
    """Filter sets by source and target language"""

    def __init__(self, source_lang_id: int, target_lang_id: int):
        self.source_lang_id = source_lang_id
        self.target_lang_id = target_lang_id

    def apply(self, stmt: Select) -> Select:
        return stmt.where(
            and_(
                Set.source_lang_id == self.source_lang_id,
                Set.target_lang_id == self.target_lang_id,
            )
        )


# Usage (optional):
# stmt = select(Item)
# for spec in [ActiveItemsOnly()]:
#     stmt = spec.apply(stmt)
# items = await db.scalars(stmt)

__all__ = [
    "BaseSpecification",
    "ActiveItemsOnly",
    "PublicSetsOnly",
    "SetsByLanguagePair",
]
