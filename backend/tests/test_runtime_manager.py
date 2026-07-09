from types import SimpleNamespace

from app.runtime_manager import DockerRuntimeManager


def make_manager() -> DockerRuntimeManager:
    settings = SimpleNamespace(
        runtime_image_context_path="/workspace/runtime",
        runtime_api_base_url="http://backend:8000",
        runtime_docker_network="devboss_default",
        runtime_dns_servers=["1.1.1.1", "8.8.8.8"],
    )
    return DockerRuntimeManager(settings)


def test_launch_engineer_sets_provider_env_vars(monkeypatch):
    manager = make_manager()
    monkeypatch.setattr(manager, "build_runtime_image", lambda image_name: None)

    captured: dict[str, object] = {}

    class FakeExistingContainer:
        status = "exited"

        def remove(self, force: bool) -> None:
            captured["removed_existing"] = force

    class FakeContainers:
        def get(self, name: str):
            return FakeExistingContainer()

        def run(self, image_name: str, **kwargs):
            captured["image_name"] = image_name
            captured["kwargs"] = kwargs
            return SimpleNamespace(name=kwargs["name"], id="container-123")

    class FakeClient:
        containers = FakeContainers()

    monkeypatch.setattr(manager, "_client", lambda: FakeClient())

    from app.enums import ModelProvider

    engineer = SimpleNamespace(
        id=7,
        docker_image="devboss-engineer:latest",
        model_provider=ModelProvider.DEEPSEEK,
        model_name="deepseek-v4-pro",
    )
    runtime = SimpleNamespace(id=11)
    container_name, container_id = manager.launch_engineer(
        engineer,
        runtime,
        "sk-example-key",
        "DEEPSEEK_API_KEY",
        "ghp_example",
        "",
        "",
        "",
    )

    assert container_name == "devboss-engineer-7-11"
    assert container_id == "container-123"
    assert captured["removed_existing"] is True
    environment = captured["kwargs"]["environment"]
    assert environment["DEVBOSS_MODEL_PROVIDER"] == "deepseek"
    assert environment["DEVBOSS_MODEL_NAME"] == "deepseek-v4-pro"
    assert environment["DEEPSEEK_API_KEY"] == "sk-example-key"
    assert "DEVBOSS_CAVEMAN_ENABLED" not in environment


def test_launch_engineer_passes_github_and_aws_env(monkeypatch):
    manager = make_manager()
    monkeypatch.setattr(manager, "build_runtime_image", lambda image_name: None)
    fake_not_found = type("FakeNotFound", (Exception,), {})
    monkeypatch.setattr("app.runtime_manager.NotFound", fake_not_found)

    captured: dict[str, object] = {}

    class FakeContainers:
        def get(self, name: str):
            raise fake_not_found()

        def run(self, image_name: str, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(name=kwargs["name"], id="container-456")

    class FakeClient:
        containers = FakeContainers()

    monkeypatch.setattr(manager, "_client", lambda: FakeClient())

    from app.enums import ModelProvider

    engineer = SimpleNamespace(
        id=8,
        docker_image="devboss-engineer:latest",
        model_provider=ModelProvider.OPENAI,
        model_name="gpt-5.4",
    )
    runtime = SimpleNamespace(id=12)
    _container_name, _container_id = manager.launch_engineer(
        engineer,
        runtime,
        "sk-openai-key",
        "OPENAI_API_KEY",
        "ghp_example_token",
        "AKID_EXAMPLE",
        "secret_example",
        "us-east-1",
    )

    environment = captured["kwargs"]["environment"]
    assert environment["OPENAI_API_KEY"] == "sk-openai-key"
    assert environment["DEVBOSS_GITHUB_TOKEN"] == "ghp_example_token"
    assert environment["AWS_ACCESS_KEY_ID"] == "AKID_EXAMPLE"
    assert environment["AWS_SECRET_ACCESS_KEY"] == "secret_example"
    assert environment["AWS_REGION"] == "us-east-1"
