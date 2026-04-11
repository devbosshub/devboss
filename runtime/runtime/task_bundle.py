from pathlib import Path


def write_task_bundle(task_root: Path, bundle: dict) -> Path:
    for file_name, contents in bundle.items():
        if file_name == "ATTACHMENTS":
            attachments_dir = task_root / "ATTACHMENTS"
            attachments_dir.mkdir(exist_ok=True)
            for index, item in enumerate(contents):
                placeholder = attachments_dir / f"{index + 1}.txt"
                placeholder.write_text(str(item), encoding="utf-8")
            continue
        file_path = task_root / file_name
        file_path.write_text(str(contents), encoding="utf-8")

    return task_root
