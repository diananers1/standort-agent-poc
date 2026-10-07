from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from standort_agent.graph.workflow import location_graph
from standort_agent.llm import groq_agents
from standort_agent.loader import load_business_profile, load_municipalities

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(autouse=True)
def isolate_local_settings(tmp_path, monkeypatch):
    # Tests must never use a developer's real credentials.
    monkeypatch.setattr(groq_agents, "ENV_PATH", tmp_path / ".env")


@pytest.fixture
def state(monkeypatch):
    monkeypatch.setenv("STANDORT_LLM_MODE", "offline")
    profile = load_business_profile(DATA_DIR / "examples" / "profil_1.json")
    dataset = load_municipalities(DATA_DIR / "municipalities.json")
    return location_graph.invoke({"raw_profile": profile, "municipalities": dataset.municipalities})


class FakeClient:
    def __init__(self, **kwargs):
        self.calls = []
        self.closed = False
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        evidence = json.loads(kwargs["messages"][1]["content"])
        if "locations" in evidence:
            content = {"explanations": [{"location": item["location"], "explanation": "Consider this signal and its limitations."} for item in evidence["locations"]]}
        else:
            content = {"recommendation": "Consider the leading location, but check actual rent and customer demand."}
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=json.dumps(content)))])

    def close(self):
        self.closed = True


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("STANDORT_LLM_MODE", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")
    instance = FakeClient()
    monkeypatch.setattr(groq_agents, "Groq", lambda **kwargs: instance)
    return instance


def test_five_llm_roles_preserve_scores_and_inputs(state, client):
    before = [item.model_dump() for item in state["rankings"]]
    result = groq_agents.enrich_with_groq(state)
    assert len(client.calls) == 5
    assert client.closed
    assert "Groq LLM analysis" in result["llm_status"]
    assert "customer_explanation" in result
    assert [item.model_dump() for item in state["rankings"]] == before
    for old, new in zip(state["rankings"], result["rankings"]):
        assert old.total_score == new.total_score
        assert old.municipality == new.municipality
        for signal in old.signals:
            assert old.signals[signal].score == new.signals[signal].score
            assert old.signals[signal].raw_value == new.signals[signal].raw_value
            assert "LLM interpretation" in new.signals[signal].reason


def test_no_key_offline_mode_makes_no_calls(state, monkeypatch):
    monkeypatch.setenv("STANDORT_LLM_MODE", "auto")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(groq_agents, "Groq", lambda **kwargs: pytest.fail("Unexpected API call"))
    assert "no LLM calls" in groq_agents.enrich_with_groq(state)["llm_status"]


def test_required_mode_reports_missing_key(state, monkeypatch):
    monkeypatch.setenv("STANDORT_LLM_MODE", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert "GROQ_API_KEY" in groq_agents.enrich_with_groq(state)["error"]


@pytest.mark.parametrize("mode", ["auto", "groq"])
def test_invalid_output_is_not_applied(state, client, monkeypatch, mode):
    monkeypatch.setenv("STANDORT_LLM_MODE", mode)
    client.chat.completions.create = lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content='{"explanations": []}'))])
    result = groq_agents.enrich_with_groq(state)
    assert "rankings" not in result
    assert "error" in result if mode == "groq" else "failed validation" in result["llm_status"]
    assert client.closed


def test_graph_runs_llm_stage(state, client, monkeypatch):
    result = location_graph.invoke({"raw_profile": state["raw_profile"], "municipalities": state["municipalities"]})
    assert len(client.calls) == 5
    assert result["customer_explanation"]


def test_dotenv_loads_local_settings(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("GROQ_API_KEY=local-test-key\nGROQ_MODEL=test-model\n", encoding="utf-8")
    monkeypatch.setattr(groq_agents, "ENV_PATH", path)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    groq_agents.load_local_settings()
    assert groq_agents.os.getenv("GROQ_API_KEY") == "local-test-key"
    assert groq_agents.os.getenv("GROQ_MODEL") == "test-model"


def test_dotenv_respects_explicit_environment(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("STANDORT_LLM_MODE=groq\n", encoding="utf-8")
    monkeypatch.setattr(groq_agents, "ENV_PATH", path)
    monkeypatch.setenv("STANDORT_LLM_MODE", "offline")
    groq_agents.load_local_settings()
    assert groq_agents.os.getenv("STANDORT_LLM_MODE") == "offline"
