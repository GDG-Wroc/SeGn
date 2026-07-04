from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    MCP_HOST: str = "127.0.0.1"
    MCP_PORT: int = 8124

    ANALOGY_LLM_BASE_URL: str | None = None
    ANALOGY_LLM_API_KEY: str | None = None
    ANALOGY_LLM_MODEL: str = "local-model"
    ANALOGY_LLM_TIMEOUT: float = 60.0
    ANALOGY_LLM_ENABLED: bool = True


config = Config()
