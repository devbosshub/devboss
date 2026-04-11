from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings


class LocalArtifactStorage:
    def __init__(self) -> None:
        self.base_path = get_settings().upload_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_upload(self, task_id: int, upload: UploadFile) -> tuple[str, str | None]:
        task_dir = self.base_path / f"task-{task_id}"
        task_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{uuid4()}-{upload.filename}"
        file_path = task_dir / file_name
        contents = upload.file.read()
        file_path.write_bytes(contents)
        return str(file_path), upload.content_type

    def write_text(self, task_id: int, name: str, body: str) -> str:
        task_dir = self.base_path / f"task-{task_id}"
        task_dir.mkdir(parents=True, exist_ok=True)
        file_path = task_dir / name
        file_path.write_text(body, encoding="utf-8")
        return str(file_path)

    def as_relative(self, path: str) -> str:
        try:
            return str(Path(path).resolve().relative_to(self.base_path))
        except ValueError:
            return path

