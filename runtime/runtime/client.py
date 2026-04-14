from __future__ import annotations

import httpx


class DevBossClient:
    def __init__(self, base_url: str) -> None:
      self.base_url = base_url.rstrip("/")
      self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip()
            if detail:
                raise RuntimeError(f"{exc}. Response body: {detail}") from exc
            raise

    def poll_next_task(self, runtime_id: int) -> dict:
        response = self.client.post("/agent/poll-next-task", json={"runtime_id": runtime_id})
        self._raise_for_status(response)
        return response.json()

    def post_log(self, task_run_id: int, body: str, action_required: bool = False) -> None:
        response = self.client.post(
            f"/agent/task-runs/{task_run_id}/logs",
            json={"body": body, "author_name": "engineer-runtime", "action_required": action_required},
        )
        self._raise_for_status(response)

    def heartbeat(self, task_run_id: int, summary: str) -> None:
        response = self.client.post(f"/agent/task-runs/{task_run_id}/heartbeat", json={"summary": summary, "status": "running"})
        self._raise_for_status(response)

    def post_outcome(self, task_run_id: int, payload: dict) -> None:
        response = self.client.post(f"/agent/task-runs/{task_run_id}/outcome", json=payload)
        self._raise_for_status(response)

    def engineer_heartbeat(
        self,
        runtime_id: int,
        container_name: str,
        container_id: str | None,
        status_message: str,
    ) -> dict:
        response = self.client.post(
            f"/engineer-runtimes/{runtime_id}/heartbeat",
            json={
                "container_name": container_name,
                "container_id": container_id,
                "status_message": status_message,
            },
        )
        self._raise_for_status(response)
        return response.json()
