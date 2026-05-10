from functools import lru_cache
from pathlib import Path
import os


def load_project_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class Settings:
    def __init__(self) -> None:
        load_project_env()
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.llm_model = os.getenv("LLM_MODEL", "")

        self.embedding_api_key = os.getenv("EMBEDDING_API_KEY", "")
        self.embedding_base_url = os.getenv("EMBEDDING_BASE_URL", "").rstrip("/")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "")
        self.request_timeout_seconds = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
        self.chroma_dir = Path(os.getenv("CHROMA_DIR", "data/chroma"))
        self.allow_llm_nudge_rewrite = os.getenv("ALLOW_LLM_NUDGE_REWRITE", "false").lower() == "true"

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_base_url and self.llm_model)

    @property
    def embedding_configured(self) -> bool:
        return bool(self.embedding_api_key and self.embedding_base_url and self.embedding_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
