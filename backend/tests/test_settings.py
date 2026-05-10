from app.settings import Settings


def test_llm_and_embedding_settings_are_independent(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("LLM_MODEL", "gpt-5-mini")
    monkeypatch.setenv("EMBEDDING_API_KEY", "embedding-key")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://embed.example/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "vendor-embed-model")

    settings = Settings()

    assert settings.llm_api_key == "llm-key"
    assert settings.llm_base_url == "https://llm.example/v1"
    assert settings.llm_model == "gpt-5-mini"
    assert settings.embedding_api_key == "embedding-key"
    assert settings.embedding_base_url == "https://embed.example/v1"
    assert settings.embedding_model == "vendor-embed-model"
    assert settings.llm_configured
    assert settings.embedding_configured


def test_openai_legacy_settings_are_not_used(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://legacy.example/v1")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)

    settings = Settings()

    assert settings.llm_api_key == ""
    assert settings.llm_base_url == ""
    assert settings.llm_model == ""
    assert settings.embedding_api_key == ""
    assert settings.embedding_base_url == ""
    assert settings.embedding_model == ""
    assert not settings.llm_configured
    assert not settings.embedding_configured
