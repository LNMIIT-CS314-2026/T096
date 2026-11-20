from typing import List
from config import Config

class FileValidator:
    """
    Section 45.4.14 <<utility>> FileValidator
    Surface-level utility that validates uploaded evidence files (FR-026, FR-027).
    """
    def __init__(self, allowedFormats: List[str] = None, maxSizeBytes: int = None):
        self.allowedFormats = (
            [fmt.lower() for fmt in allowedFormats]
            if allowedFormats is not None
            else [fmt.lower() for fmt in Config.ALLOWED_FORMATS]
        )
        self.maxSizeBytes = maxSizeBytes if maxSizeBytes is not None else Config.MAX_SIZE_BYTES

    def checkFormat(self, fileType: str) -> bool:
        """Table 25 checkFormat: returns true if the format is allowed."""
        if not fileType:
            return False
        clean_ext = fileType.lower().strip().lstrip(".")
        return clean_ext in self.allowedFormats

    def checkSize(self, fileSize: int) -> bool:
        """Table 25 checkSize: returns true if size <= maxSizeBytes."""
        if fileSize is None or fileSize <= 0:
            return False
        return fileSize <= self.maxSizeBytes
