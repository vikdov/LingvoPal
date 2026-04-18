# backend/app/core/token_types.py
"""
Typed JWT payload model.

Centralises claim names so changing a claim is a one-line edit,
not a grep-and-pray across the codebase.
"""

from pydantic import BaseModel, ConfigDict


class AccessTokenPayload(BaseModel):
    """
    Claims present in every LingvoPal access token.

    sub  — user ID (string per JWT spec, cast to int on read)
    role — coarse permission level; avoids a DB lookup in hot paths
    iat  — issued-at (unix timestamp, added by encode step)
    exp  — expiry   (unix timestamp, added by encode step)
    """

    model_config = ConfigDict(frozen=True)

    sub: str  # str in the token, int in the app — convert at boundary
    role: str  # "user" | "admin"

    @property
    def user_id(self) -> int:
        """Convenience: typed user ID without callers remembering to cast."""
        return int(self.sub)


__all__ = ["AccessTokenPayload"]
