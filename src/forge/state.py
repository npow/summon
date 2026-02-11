"""ForgeState TypedDict — the single state object flowing through the pipeline."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from forge.schemas.spec import IdeaSpec
from forge.schemas.prd import PRD
from forge.schemas.sdd import SDD
from forge.schemas.hld import HLD, ComponentDesign
from forge.schemas.component import ComponentResult
from forge.schemas.quality import GateResult
from forge.schemas.release import ReleaseInfo


class ForgeState(TypedDict, total=False):
    # Input
    raw_idea: str

    # Stage 1: Idea Refinement
    ambiguities: list[str]
    clarifications: list[str]
    spec: dict[str, Any]  # Serialized IdeaSpec — immutable after Stage 1

    # Stage 2: Planning
    prd: dict[str, Any]
    sdd: dict[str, Any]
    _critic_result: dict[str, Any]
    critic_feedback: str
    planning_approved: bool

    # Stage 3: Design
    hld: dict[str, Any]
    _split_result: dict[str, Any]
    components: list[dict[str, Any]]

    # Stage 4: Implementation (parallel results aggregated via operator.add)
    component_results: Annotated[list[dict[str, Any]], operator.add]
    _lld_result: dict[str, Any]
    _code_result: dict[str, Any]
    _review_result: dict[str, Any]
    _review_retries: int

    # Stage 5: Testing
    _integration_result: dict[str, Any]
    integration_code: str
    _test_result: dict[str, Any]
    test_code: str
    test_results: str
    bugs: list[str]
    tests_passing: bool
    _fix_result: dict[str, Any]
    project_files: str
    source_files: str

    # Stage 5: Import validation
    import_errors: str
    import_validation_passing: bool
    _import_fix_result: dict[str, Any]
    import_fix_source_files: str

    # Stage 5: Degeneracy detection & regeneration
    degenerate_files: str  # JSON list of {file, issue, detail}
    degeneracy_detected: bool
    _regen_result: dict[str, Any]

    # Stage 5: Acceptance testing
    acceptance_criteria: str
    _acceptance_gen_result: dict[str, Any]
    acceptance_test_script: str
    _acceptance_test_gen_result: dict[str, Any]
    acceptance_test_results: str
    acceptance_tests_passing: bool
    _acceptance_fix_result: dict[str, Any]

    # Stage 6: Release
    _package_result: dict[str, Any]
    _package_files: list[str]
    _docs_result: dict[str, Any]
    _github_result: dict[str, Any]
    _publish_result: dict[str, Any]
    release_info: dict[str, Any]

    # Supervisor / control flow
    current_stage: str
    gate_results: list[dict[str, Any]]
    stage_retries: dict[str, int]
    error: str | None

    # Workspace
    workspace_path: str
