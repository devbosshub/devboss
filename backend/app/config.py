from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dev Boss API"
    database_url: str = "sqlite:///./devboss.db"
    upload_dir: str = "uploads"
    default_poll_interval_seconds: int = 30
    engineer_heartbeat_timeout_seconds: int = 90
    runtime_docker_network: str = "devboss_default"
    runtime_docker_dns_servers: str = "1.1.1.1,8.8.8.8"
    runtime_api_base_url: str = "http://backend:8000"
    runtime_image_context_path: str = "/workspace/runtime"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir).resolve()

    @property
    def runtime_dns_servers(self) -> list[str]:
        return [server.strip() for server in self.runtime_docker_dns_servers.split(",") if server.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
