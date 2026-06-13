# backend/app/services/image_search_service.py
"""
Image search using Unsplash, Pexels, or Pixabay.

Images are downloaded and uploaded to S3 immediately after search so that
returned URLs are permanent. External URLs (Pexels especially) expire;
storing in S3 eliminates link rot and keeps user data off third-party servers.

thumbnail_url stays external — it's only used briefly in the suggestion picker
and is never stored long-term.
"""

import asyncio
import hashlib
import logging
from typing import TypedDict

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_CONTENT_TYPE_TO_EXT = {
    "jpeg": "jpg",
    "jpg": "jpg",
    "png": "png",
    "webp": "webp",
    "gif": "gif",
}


class ImageSuggestion(TypedDict):
    """Image search result metadata."""

    url: str  # S3 URL after persist_images; external URL on fetch failure
    thumbnail_url: str | None  # External thumbnail (picker display only, not stored)
    source: str


def _image_s3_key(source_url: str, ext: str) -> str:
    """Deterministic S3 key for an image. Same source URL → same key → no duplicate uploads."""
    digest = hashlib.sha256(source_url.encode()).hexdigest()[:16]
    return f"images/{digest}.{ext}"


class ImageSearchService:
    """Find relevant images for vocabulary terms."""

    def __init__(self):
        from app.services.storage import StorageService

        settings = get_settings()
        self.provider = settings.IMAGE_SEARCH_PROVIDER
        self.api_key = settings.IMAGE_SEARCH_API_KEY
        self.client = httpx.AsyncClient(timeout=15.0)
        self._storage = StorageService()

    async def search_images(
        self,
        term: str,
        count: int = 3,
    ) -> list[ImageSuggestion]:
        """
        Search for images, download them, upload to S3.

        Returns S3 URLs so accepted images are permanently stored and
        independent of the source provider.
        """
        if not term or not term.strip():
            return []

        try:
            if self.provider == "unsplash":
                raw = await self._unsplash_search(term, count)
            elif self.provider == "pexels":
                raw = await self._pexels_search(term, count)
            elif self.provider == "pixabay":
                raw = await self._pixabay_search(term, count)
            else:
                logger.warning(f"Unknown image provider: {self.provider}")
                return []

            return await self._persist_images(raw)

        except Exception as e:
            logger.error(f"Image search failed for '{term}': {e}")
            return []

    async def _persist_images(self, results: list[ImageSuggestion]) -> list[ImageSuggestion]:
        """Download external images and re-upload to S3 in parallel. Deduplicates by source URL."""

        async def persist_one(suggestion: ImageSuggestion) -> ImageSuggestion:
            source_url = suggestion["url"]
            try:
                response = await self.client.get(source_url)
                response.raise_for_status()

                content_type = (
                    response.headers.get("content-type", "image/jpeg").split(";")[0].strip()
                )
                raw_ext = content_type.split("/")[-1].lower()
                ext = _CONTENT_TYPE_TO_EXT.get(raw_ext, "jpg")

                key = _image_s3_key(source_url, ext)
                cached = await self._storage.get_url_if_exists(key)
                if cached:
                    s3_url = cached
                else:
                    s3_url = await self._storage.upload_at_key(response.content, key, content_type)

                return ImageSuggestion(
                    url=s3_url,
                    thumbnail_url=suggestion.get("thumbnail_url"),
                    source=suggestion.get("source", ""),
                )
            except Exception as e:
                logger.warning(f"Failed to persist image to S3, keeping external URL: {e}")
                return suggestion

        persisted = await asyncio.gather(*[persist_one(r) for r in results])
        return list(persisted)

    async def _unsplash_search(self, term: str, count: int) -> list[ImageSuggestion]:
        """Search Unsplash API."""
        try:
            response = await self.client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": term, "per_page": count, "client_id": self.api_key},
            )
            response.raise_for_status()
            data = response.json()

            return [
                ImageSuggestion(
                    url=photo["urls"]["regular"],
                    thumbnail_url=photo["urls"]["thumb"],
                    source="unsplash",
                )
                for photo in data.get("results", [])
            ]
        except httpx.HTTPStatusError as e:
            logger.error("Unsplash search failed", extra={"status": e.response.status_code})
            return []
        except Exception as e:
            logger.error("Unsplash search failed", extra={"error": type(e).__name__})
            return []

    async def _pexels_search(self, term: str, count: int) -> list[ImageSuggestion]:
        """Search Pexels API."""
        try:
            response = await self.client.get(
                "https://api.pexels.com/v1/search",
                params={"query": term, "per_page": count},
                headers={"Authorization": self.api_key},
            )
            response.raise_for_status()
            data = response.json()

            return [
                ImageSuggestion(
                    url=photo["src"]["large"],
                    thumbnail_url=photo["src"]["small"],
                    source="pexels",
                )
                for photo in data.get("photos", [])
            ]
        except httpx.HTTPStatusError as e:
            logger.error("Pexels search failed", extra={"status": e.response.status_code})
            return []
        except Exception as e:
            logger.error("Pexels search failed", extra={"error": type(e).__name__})
            return []

    async def _pixabay_search(self, term: str, count: int) -> list[ImageSuggestion]:
        """Search Pixabay API."""
        try:
            response = await self.client.get(
                "https://pixabay.com/api",
                params={
                    "q": term,
                    "per_page": count,
                    "key": self.api_key,
                    "image_type": "photo",
                },
            )
            response.raise_for_status()
            data = response.json()

            return [
                ImageSuggestion(
                    url=hit["webformatURL"],
                    thumbnail_url=hit.get("previewURL"),
                    source="pixabay",
                )
                for hit in data.get("hits", [])
            ]
        except httpx.HTTPStatusError as e:
            logger.error("Pixabay search failed", extra={"status": e.response.status_code})
            return []
        except Exception as e:
            logger.error("Pixabay search failed", extra={"error": type(e).__name__})
            return []

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


__all__ = ["ImageSearchService", "ImageSuggestion"]
