"""Basic smoke tests — no live API calls."""
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture(autouse=True)
def mock_anthropic():
    fake = MagicMock()
    fake.content = [MagicMock(text="mocked response")]
    fake.usage = MagicMock(input_tokens=5, output_tokens=10)
    with patch("anthropic.Anthropic") as cls:
        cls.return_value.messages.create.return_value = fake
        with patch("agents.base.client", cls.return_value):
            yield cls.return_value


@pytest.fixture(autouse=True)
def mock_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    db = tmp_path / "test.db"
    import config as cfg
    monkeypatch.setattr(cfg.config, "db_path", str(db))
    import memory.store as ms
    ms.memory.__init__()
    yield ms.memory


from agents import (
    CodeGenAgent, CodeReviewAgent, DebuggerAgent, ResearchAgent,
    OptimizerAgent, DocumenterAgent, RequirementsAgent,
    ReflectorAgent, AgentBuilderAgent, ScaffolderAgent,
)

ALL = [
    CodeGenAgent, CodeReviewAgent, DebuggerAgent, ResearchAgent,
    OptimizerAgent, DocumenterAgent, RequirementsAgent,
    ReflectorAgent, AgentBuilderAgent, ScaffolderAgent,
]


@pytest.mark.parametrize("cls", ALL)
def test_agent_call(cls, mock_anthropic):
    agent = cls()
    result = agent.call("test prompt")
    assert isinstance(result, str) and len(result) > 0


def test_unique_names():
    names = [cls().name for cls in ALL]
    assert len(names) == len(set(names))


def test_scaffolder_parses_valid_json(tmp_path, mock_anthropic):
    import json
    project = {
        "project_name": "test_project",
        "description": "A test",
        "files": {"main.py": "print('hello')", "requirements.txt": "flask"}
    }
    mock_anthropic.messages.create.return_value.content[0].text = json.dumps(project)
    agent = ScaffolderAgent()
    zip_path = agent.scaffold("build something", output_dir=str(tmp_path))
    assert zip_path.endswith(".zip")
    import os
    assert os.path.exists(zip_path)
