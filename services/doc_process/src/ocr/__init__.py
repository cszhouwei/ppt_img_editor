"""OCR service module"""
from .mock_provider import MockOCRProvider
from .azure_provider import AzureOCRProvider
from .base import OCRProvider, OCRCandidate

__all__ = ["MockOCRProvider", "AzureOCRProvider", "OCRProvider", "OCRCandidate"]
