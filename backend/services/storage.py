import os
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

class StorageService:
    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        self.local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "all resumes")
        
        # Ensure local dir exists for fallback
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir, exist_ok=True)

        self.client = None
        if self.bucket_name:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
            except (DefaultCredentialsError, Exception) as e:
                print(f"Warning: Cloud Storage initialized but credentials missing or error occurred: {e}")
                print("Falling back to local storage.")
                self.client = None

    def upload_file(self, file_content, filename, user_id, category="resumes"):
        """Uploads a file to GCS or local storage. Returns the storage path."""
        relative_path = f"{category}/{user_id}/{filename}"
        
        if self.client and self.bucket_name:
            # Upload to GCS
            blob = self.bucket.blob(relative_path)
            blob.upload_from_string(file_content)
            return f"gs://{self.bucket_name}/{relative_path}"
        else:
            # Save to local file system
            full_path = os.path.join(self.local_dir, user_id, filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file_content)
            return full_path

    def get_file_content(self, storage_path):
        """Retrieves file content from GCS or local storage."""
        if storage_path.startswith("gs://"):
            if not self.client:
                raise Exception("Attempted to read from GCS but client is not initialized")
            
            # gs://bucket/path/to/file
            parts = storage_path.replace("gs://", "").split("/")
            bucket_name = parts[0]
            blob_path = "/".join(parts[1:])
            
            blob = self.client.bucket(bucket_name).blob(blob_path)
            return blob.download_as_bytes()
        else:
            # Local path
            if os.path.exists(storage_path):
                with open(storage_path, "rb") as f:
                    return f.read()
            return None

    def get_download_url(self, storage_path):
        """Returns a signed URL for GCS or a local relative path for frontend."""
        if storage_path.startswith("gs://"):
            if not self.client:
                return None
            
            parts = storage_path.replace("gs://", "").split("/")
            blob_path = "/".join(parts[1:])
            blob = self.bucket.blob(blob_path)
            
            # Generate a signed URL valid for 1 hour
            return blob.generate_signed_url(expiration=3600)
        else:
            # For local, we'd need a backend route to serve the file
            # or return a specific identifier the frontend can use
            return storage_path

# Singleton instance
storage_service = StorageService()
