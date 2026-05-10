import os


class StorageService:
    """Local filesystem storage only (no Google Cloud Storage)."""

    def __init__(self):
        self.local_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "all resumes",
        )
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir, exist_ok=True)

    def upload_file(self, file_content, filename, user_id, category="resumes"):
        """Saves under all resumes/<category>/<user_id>/<filename>. Returns absolute path."""
        relative_path = f"{category}/{user_id}/{filename}"
        full_path = os.path.join(self.local_dir, user_id, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_content)
        return full_path

    def get_file_content(self, storage_path):
        """Reads bytes from a local path. gs:// URLs are not supported."""
        if storage_path.startswith("gs://"):
            raise ValueError(
                "Google Cloud Storage is disabled; migrate paths to local files."
            )
        if os.path.exists(storage_path):
            with open(storage_path, "rb") as f:
                return f.read()
        return None

    def get_download_url(self, storage_path):
        """Returns local path for API/frontend to serve."""
        if storage_path.startswith("gs://"):
            return None
        return storage_path


storage_service = StorageService()
