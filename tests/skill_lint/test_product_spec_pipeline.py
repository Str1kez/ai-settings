from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_SKILL = REPO_ROOT / "skills/product-spec-pipeline/SKILL.md"
SPEC_ALIAS_SKILL = REPO_ROOT / "skills/spec/SKILL.md"

BRAINSTORM_PHASE = "## Phase 2: Brainstorm the idea"
GRILLING_PHASE = "## Phase 5: Grill the selected direction"


def _brainstorm_phase(content: str) -> str:
    start = content.index(BRAINSTORM_PHASE)
    end = content.index("\n## ", start + len(BRAINSTORM_PHASE))
    return content[start:end]


def test_pipeline_brainstorms_on_its_own_before_grilling() -> None:
    content = PIPELINE_SKILL.read_text(encoding="utf-8")
    phase = _brainstorm_phase(content)

    assert content.index(BRAINSTORM_PHASE) < content.index(GRILLING_PHASE)
    assert "2-3 materially different product directions" in phase
    assert "select or approve 1 direction" in phase
    assert "<run-dir>/brainstorm.md" in phase
    assert "Do not commit" in phase


def test_pipeline_does_not_depend_on_brainstorming_skill() -> None:
    content = PIPELINE_SKILL.read_text(encoding="utf-8")
    phase = _brainstorm_phase(content)

    assert "embedded-mode" not in content
    assert "`brainstorming`" not in content
    assert "brainstorming" not in phase.lower()


def test_spec_alias_invokes_product_spec_pipeline():
    content = SPEC_ALIAS_SKILL.read_text(encoding="utf-8")

    assert "`product-spec-pipeline`" in content
    assert "Pass the user's complete prompt" in content


def test_pipeline_analyzes_existing_or_empty_project_before_brainstorming():
    content = PIPELINE_SKILL.read_text(encoding="utf-8")

    project_analysis = content.index("### Analyze the project first")
    brainstorming_phase = content.index("## Phase 2: Brainstorm the idea")

    assert project_analysis < brainstorming_phase
    assert "<run-dir>/project-context.md" in content
    assert "greenfield" in content
    assert "non-empty" in content


def test_pipeline_offers_research_and_dispatches_one_fresh_worker_per_selection():
    content = PIPELINE_SKILL.read_text(encoding="utf-8")

    research_selection = content.index("## Phase 3: Select deep research")
    research_execution = content.index("## Phase 4: Run selected research")
    grilling_phase = content.index("## Phase 5: Grill the selected direction")

    assert research_selection < research_execution < grilling_phase
    assert "one fresh agent session per selected track" in content
    assert "orca orchestration task-create" in content
    assert "orca orchestration dispatch --inject" in content
    assert "maximum of 3 research workers concurrently" in content
    assert "<run-dir>/research-summary.md" in content
