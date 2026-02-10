"""Tests for Pydantic schemas."""

from forge.schemas.spec import IdeaSpec, FunctionalRequirement
from forge.schemas.prd import PRD, UserStory
from forge.schemas.sdd import SDD, TechChoice
from forge.schemas.hld import HLD, ComponentDesign
from forge.schemas.component import ComponentResult, FileOutput
from forge.schemas.quality import GateResult
from forge.schemas.release import ReleaseInfo


def test_idea_spec():
    spec = IdeaSpec(
        project_name="my-tool",
        one_liner="A tool that does things",
        target_users=["developers"],
        language="python",
        package_type="cli",
        functional_requirements=[
            FunctionalRequirement(id="FR-001", description="Does X", priority="high"),
            FunctionalRequirement(id="FR-002", description="Does Y", priority="medium"),
            FunctionalRequirement(id="FR-003", description="Does Z", priority="low"),
        ],
    )
    assert spec.project_name == "my-tool"
    data = spec.model_dump()
    assert len(data["functional_requirements"]) == 3


def test_prd():
    prd = PRD(
        project_name="my-tool",
        vision="A great tool",
        user_stories=[
            UserStory(
                id="US-001",
                persona="developer",
                action="run the CLI",
                benefit="save time",
                acceptance_criteria=["it works"],
            )
        ],
        mvp_scope=["US-001"],
        success_metrics=["100 downloads"],
    )
    assert prd.project_name == "my-tool"


def test_gate_result():
    result = GateResult(
        stage="idea_refinement",
        passed=True,
        score=0.85,
        conformance=0.9,
        quality=0.85,
        coherence=0.9,
        scope_creep=0.1,
        feedback="Good work",
    )
    assert result.passed
    assert result.score == 0.85


def test_component_result():
    result = ComponentResult(
        component_id="comp-001",
        files=[FileOutput(path="src/main.py", content="print('hi')")],
    )
    assert result.component_id == "comp-001"
    assert len(result.files) == 1
