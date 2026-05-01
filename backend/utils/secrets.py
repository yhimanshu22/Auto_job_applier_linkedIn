import os
from google.cloud import secretmanager
from google.auth.exceptions import DefaultCredentialsError

def get_secret(secret_id, version_id="latest"):
    """
    Fetches a secret from Google Cloud Secret Manager.
    Falls back to environment variables if not in production or if GCP fails.
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    env = os.getenv("ENV", "development")
    
    # Always try environment variable first for local dev
    env_val = os.getenv(secret_id)
    if env != "production" and env_val:
        return env_val

    if not project_id:
        return env_val

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except (DefaultCredentialsError, Exception) as e:
        # Fallback to env var if GCP access fails
        if env_val:
            return env_val
        return None

def load_all_secrets(secret_names: list):
    """Loads multiple secrets into os.environ for convenience."""
    for name in secret_names:
        val = get_secret(name)
        if val:
            os.environ[name] = val
