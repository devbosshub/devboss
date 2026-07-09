from pathlib import Path
import socket

from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    api_base_url: str = "http://backend:8000"
    engineer_id: int = 1
    runtime_id: int = 1
    poll_interval_seconds: int = 15
    workspace_dir: str = "/tmp/devboss-runtime"
    opencode_command: str = "opencode"
    dry_run: bool = False
    heartbeat_interval_seconds: int = 60
    heartbeat_only: bool = False
    container_name: str = ""
    github_token: str = ""
    model_provider: str = "deepseek"
    model_name: str = "deepseek-v4-pro"

    model_config = SettingsConfigDict(env_prefix="DEVBOSS_", extra="ignore")

    @property
    def workspace_path(self) -> Path:
        path = Path(self.workspace_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def effective_container_name(self) -> str:
        return self.container_name or socket.gethostname()
