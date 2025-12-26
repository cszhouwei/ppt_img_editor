"""OCR service module"""
from .mock_provider import MockOCRProvider
from .base import OCRProvider, OCRCandidate

__all__ = ["MockOCRProvider", "OCRProvider", "OCRCandidate"]
