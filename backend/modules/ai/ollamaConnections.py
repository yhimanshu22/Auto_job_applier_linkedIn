"""Local Ollama client for Easy Apply question answering (OpenAI-compatible API)."""

from openai import OpenAI

from config.config_bridge import llm_api_key, llm_api_url, llm_model, use_AI
from modules.ai.openaiConnections import ai_close_openai_client, ai_get_models_list, apiCheckInstructions
from modules.helpers import print_lg, critical_error_log


def _base_url() -> str:
    base = (llm_api_url or "http://127.0.0.1:11434/v1").strip().rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    return base


def _resolve_model() -> str:
    explicit = (llm_model or "").strip()
    if explicit:
        return explicit
    from linkedin_automation.ollama_runtime import resolve_ollama_model

    return resolve_ollama_model()


def ollama_create_client() -> OpenAI:
    """Create an OpenAI SDK client pointed at the local Ollama server."""
    try:
        print_lg("Creating Ollama client for Easy Apply AI...")
        if not use_AI:
            raise ValueError(
                "AI is not enabled! Set `use_AI` to true in dashboard secrets."
            )

        api_key = (llm_api_key or "ollama").strip() or "ollama"
        model = _resolve_model()
        client = OpenAI(base_url=_base_url(), api_key=api_key)

        models = ai_get_models_list(client)
        if models and isinstance(models[0], str) and models[0] == "error":
            raise ValueError(models[1])
        ids = [getattr(m, "id", str(m)) for m in (models or [])]
        if ids and model not in ids:
            # Allow partial match (e.g. tag drift).
            match = next((mid for mid in ids if mid.split(":")[0] == model.split(":")[0]), None)
            if match:
                model = match
            else:
                print_lg(
                    f"Warning: model {model!r} not in Ollama tag list; attempting anyway."
                )

        print_lg("---- SUCCESSFULLY CREATED OLLAMA CLIENT! ----")
        print_lg(f"Using API URL: {_base_url()}")
        print_lg(f"Using Model: {model}")
        return client
    except Exception as e:
        critical_error_log(
            f"Error occurred while creating Ollama client. {apiCheckInstructions}", e
        )
        raise


__all__ = ["ollama_create_client", "ai_close_openai_client"]