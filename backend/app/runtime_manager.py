from __future__ import annotations

from pathlib import Path

import docker
from docker.errors import APIError, BuildError, DockerException, NotFound
from fastapi import HTTPException

from app.config import Settings
from app.models import Engineer, EngineerRuntime


class DockerRuntimeManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _client(self):
        try:
            return docker.from_env()
        except DockerException as exc:
            raise HTTPException(status_code=503, detail=f"Docker is not available: {exc}") from exc

    def build_runtime_image(self, image_name: str) -> None:
        client = self._client()
        context_path = Path(self.settings.runtime_image_context_path)
        if not context_path.exists():
            raise HTTPException(status_code=500, detail=f"Runtime image context not found: {context_path}")
        try:
            client.images.build(path=str(context_path), tag=image_name)
        except (BuildError, APIError) as exc:
            raise HTTPException(status_code=500, detail=f"Failed to build runtime image: {exc}") from exc

    def launch_engineer(
        self,
        engineer: Engineer,
        runtime: EngineerRuntime,
        codex_auth_json: str,
        github_token: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
    ) -> tuple[str, str]:
        client = self._client()
        container_name = f"devboss-engineer-{engineer.id}-{runtime.id}"

        try:
            existing = client.containers.get(container_name)
            if existing.status == "running":
                raise HTTPException(status_code=400, detail="Engineer runtime is already running")
            existing.remove(force=True)
        except NotFound:
            pass
        except APIError as exc:
            raise HTTPException(status_code=500, detail=f"Failed to inspect existing runtime: {exc}") from exc

        self.build_runtime_image(engineer.docker_image)

        environment = {
            "DEVBOSS_API_BASE_URL": self.settings.runtime_api_base_url,
            "DEVBOSS_ENGINEER_ID": str(engineer.id),
            "DEVBOSS_RUNTIME_ID": str(runtime.id),
            "DEVBOSS_HEARTBEAT_INTERVAL_SECONDS": "60",
            "DEVBOSS_CONTAINER_NAME": container_name,
            "DEVBOSS_HEARTBEAT_ONLY": "false",
            "DEVBOSS_CODEX_AUTH_JSON": codex_auth_json,
            "DEVBOSS_GITHUB_TOKEN": github_token,
            "DEVBOSS_DRY_RUN": "false",
            "AWS_ACCESS_KEY_ID": aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": aws_secret_access_key,
            "AWS_DEFAULT_REGION": aws_region,
            "AWS_REGION": aws_region,
        }

        try:
            container = client.containers.run(
                engineer.docker_image,
                detach=True,
                name=container_name,
                network=self.settings.runtime_docker_network,
                dns=self.settings.runtime_dns_servers or None,
                restart_policy={"Name": "unless-stopped"},
                environment=environment,
                labels={
                    "devboss.engineer_id": str(engineer.id),
                    "devboss.runtime_id": str(runtime.id),
                    "devboss.managed": "true",
                },
            )
        except APIError as exc:
            raise HTTPException(status_code=500, detail=f"Failed to launch engineer runtime: {exc}") from exc

        return container.name, container.id

    def stop_engineer_runtime(self, runtime: EngineerRuntime) -> None:
        container_name = runtime.container_name or f"devboss-engineer-{runtime.engineer_id}-{runtime.id}"
        client = self._client()
        try:
            container = client.containers.get(container_name)
        except NotFound:
            return
        except APIError as exc:
            raise HTTPException(status_code=500, detail=f"Failed to inspect runtime: {exc}") from exc

        try:
            container.stop(timeout=10)
            container.remove(force=True)
        except APIError as exc:
            raise HTTPException(status_code=500, detail=f"Failed to stop engineer runtime: {exc}") from exc
