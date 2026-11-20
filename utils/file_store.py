import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from config import Config

class FileStoreAdapter:
    """
    Section 47.2.7 File Store Adapter (IFileStore)
    Surface-level utility that handles local file I/O for evidence binaries.
    """
    def __init__(self, upload_folder: Path = None):
        self.upload_folder = Path(upload_folder or Config.UPLOAD_FOLDER)
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def save(self, file_storage) -> str:
        """Saves file to disk and returns the relative storage path."""
        original_name = secure_filename(file_storage.filename or "evidence")
        filename = f"{uuid.uuid4().hex[:8]}_{original_name}"
        dest_path = self.upload_folder / filename
        file_storage.save(str(dest_path))
        return str(dest_path)

    def open(self, storagePath: str) -> Path:
        p = Path(storagePath)
        if not p.is_file():
            p = self.upload_folder / Path(storagePath).name
        if not p.is_file():
            raise FileNotFoundError(f"File not found: {storagePath}")
        return p

    def remove(self, storagePath: str) -> bool:
        try:
            p = Path(storagePath)
            if p.is_file():
                p.unlink()
                return True
            p = self.upload_folder / Path(storagePath).name
            if p.is_file():
                p.unlink()
                return True
        except Exception:
            pass
        return False
