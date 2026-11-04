"""init-project.sh --claude-models / --opencode-models: personal agents with
concrete models inside the project, kept out of its git history.

The templates come from a fixture repo, so the tests don't depend on which
templates the real repo holds."""

import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.helpers import (
    copy_scripts,
    git,
    git_track,
    isolated_git_env,
    run_unchecked,
    write,
)

CLAUDE_FLAG = "frontier=opus,standard=sonnet"
OPENCODE_FLAG = "frontier=anthropic/opus,standard=openai/gpt"
FOREIGN = "---\ndescription: mine\n---\nMy own agent.\n"


def _template(name: str, level: str, effort: str | None, body: str = "Do the job.") -> str:
    effort_line = f"effort: {effort}\n" if effort else ""
    return (
        f"---\nname: {name}\ndescription: Use for {name} work.\n"
        f"model: {level}\n{effort_line}tools: [Read, Grep]\n---\n\n{body}\n"
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """An ai-settings repo with a frontier and a standard template."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    write(repo / "agents/reviewer/AGENT.md", _template("reviewer", "frontier", "high"))
    write(repo / "agents/worker/AGENT.md", _template("worker", "standard", None))
    git_track(repo, "agents")
    return repo


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def project(tmp_path: Path, home: Path) -> Path:
    """A project in a subdirectory of a git repo."""
    top = tmp_path / "top"
    project = top / "services/api"
    project.mkdir(parents=True)
    git(top, home, "init", "-q")
    return project


def _init(repo: Path, home: Path, project: Path, *flags: str) -> tuple[int, str]:
    result = run_unchecked(
        [repo / "scripts/init-project.sh", *flags, project],
        home,
        **isolated_git_env(home),
    )
    return result.returncode, result.stderr


def _split(path: Path) -> tuple[dict[str, Any], str, str]:
    """YAML fields, body and the raw frontmatter of a markdown agent."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    assert match, f"{path}: no frontmatter"
    return yaml.safe_load(match.group(1)), match.group(2), match.group(1)


CLAUDE_DIR = ".claude/agents"
OPENCODE_DIR = ".opencode/agents"


def test_claude_models_become_marked_project_agents_with_the_level_recorded(
    repo: Path, home: Path, project: Path
) -> None:
    code, _ = _init(repo, home, project, "--claude-models", CLAUDE_FLAG)

    fields, body, raw = _split(project / CLAUDE_DIR / "reviewer.md")
    assert code == 0
    assert fields["model"] == "opus"
    assert fields["effort"] == "high"
    assert fields["name"] == "reviewer"
    assert "# managed-by: ai-settings" in raw
    assert "# model-level: frontier" in raw
    assert body.strip() == "Do the job."
    worker, _, worker_raw = _split(project / CLAUDE_DIR / "worker.md")
    assert worker["model"] == "sonnet"
    assert "effort" not in worker
    assert "# model-level: standard" in worker_raw
    assert not (project / OPENCODE_DIR).exists()


def test_opencode_models_become_subagents_with_provider_model_and_permissions(
    repo: Path, home: Path, project: Path
) -> None:
    code, _ = _init(repo, home, project, "--opencode-models", OPENCODE_FLAG)

    fields, _, raw = _split(project / OPENCODE_DIR / "reviewer.md")
    assert code == 0
    assert fields["model"] == "anthropic/opus"
    assert fields["mode"] == "subagent"
    assert "effort" not in fields
    assert [(rule["action"], rule["effect"]) for rule in fields["permissions"]] == [
        ("read", "allow"),
        ("grep", "allow"),
        ("edit", "deny"),
        ("shell", "deny"),
    ]
    assert "# model-level: frontier" in raw
    worker, _, _ = _split(project / OPENCODE_DIR / "worker.md")
    assert worker["model"] == "openai/gpt"


def test_every_project_agent_has_exactly_one_exclude_line_after_two_runs(repo: Path, home: Path, project: Path) -> None:
    for _ in range(2):
        code, _ = _init(repo, home, project, "--claude-models", CLAUDE_FLAG, "--opencode-models", OPENCODE_FLAG)
        assert code == 0

    top = project.parent.parent
    exclude = (top / ".git/info/exclude").read_text(encoding="utf-8").splitlines()
    names = ("reviewer", "worker")
    for directory in (CLAUDE_DIR, OPENCODE_DIR):
        for name in names:
            assert exclude.count(f"/services/api/{directory}/{name}.md") == 1
    status = git(top, home, "status", "--porcelain", "--untracked-files=all")
    assert ".claude/agents" not in status
    assert ".opencode/agents" not in status


@pytest.mark.parametrize(
    ("flags", "message"),
    [
        (("--claude-models", "frontier=opus,standard=sonnet,huge=x"), "huge"),
        (("--claude-models", "frontier=opus"), "standard"),
        (("--claude-models", "frontier,standard=sonnet"), "frontier"),
        (("--opencode-models", "frontier=anthropic/opus,standard=gpt"), "provider/model"),
        (("--claude-models", CLAUDE_FLAG, "--opencode-models", "frontier=a/b"), "standard"),
    ],
)
def test_bad_model_flags_fail_and_create_no_agents(
    repo: Path, home: Path, project: Path, flags: tuple[str, ...], message: str
) -> None:
    code, log = _init(repo, home, project, *flags)

    assert code != 0
    assert message in log
    assert not (project / ".claude").exists()
    assert not (project / ".opencode").exists()


def test_foreign_file_under_an_agent_name_is_left_alone_and_reported(repo: Path, home: Path, project: Path) -> None:
    write(project / CLAUDE_DIR / "worker.md", FOREIGN)

    code, log = _init(repo, home, project, "--claude-models", CLAUDE_FLAG)

    assert code == 0
    assert (project / CLAUDE_DIR / "worker.md").read_text(encoding="utf-8") == FOREIGN
    assert "worker.md" in log and "skip" in log.lower()
    assert (project / CLAUDE_DIR / "reviewer.md").is_file()
    exclude = (project.parent.parent / ".git/info/exclude").read_text(encoding="utf-8")
    assert "worker.md" not in exclude


def test_agent_already_tracked_by_git_gets_a_warning_with_the_untrack_command(
    repo: Path, home: Path, project: Path
) -> None:
    _init(repo, home, project, "--claude-models", CLAUDE_FLAG)
    git(project, home, "add", "-f", f"{CLAUDE_DIR}/reviewer.md")

    code, log = _init(repo, home, project, "--claude-models", CLAUDE_FLAG)

    assert code == 0
    assert f"git rm --cached {CLAUDE_DIR}/reviewer.md" in log


def test_outside_git_agents_are_created_with_a_warning_to_rerun_after_git_init(
    repo: Path, home: Path, tmp_path: Path
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()

    code, log = _init(repo, home, plain, "--claude-models", CLAUDE_FLAG)

    assert code == 0
    assert (plain / CLAUDE_DIR / "reviewer.md").is_file()
    assert "git init" in log


def test_without_flags_no_agents_are_created_and_the_run_succeeds(repo: Path, home: Path, project: Path) -> None:
    code, log = _init(repo, home, project)

    assert code == 0
    assert not (project / ".claude").exists()
    assert not (project / ".opencode").exists()
    assert "--claude-models" in log


def test_template_gone_from_the_repo_takes_its_project_agent_along(repo: Path, home: Path, project: Path) -> None:
    write(project / CLAUDE_DIR / "mine.md", FOREIGN)
    _init(repo, home, project, "--claude-models", CLAUDE_FLAG)
    shutil.rmtree(repo / "agents/worker")

    code, _ = _init(repo, home, project, "--claude-models", CLAUDE_FLAG)

    assert code == 0
    assert sorted(p.name for p in (project / CLAUDE_DIR).iterdir()) == ["mine.md", "reviewer.md"]


def test_changed_template_reaches_the_project_on_rerun(repo: Path, home: Path, project: Path) -> None:
    _init(repo, home, project, "--claude-models", CLAUDE_FLAG)
    write(repo / "agents/worker/AGENT.md", _template("worker", "frontier", "low", body="New prompt."))

    code, _ = _init(repo, home, project, "--claude-models", CLAUDE_FLAG)

    fields, body, raw = _split(project / CLAUDE_DIR / "worker.md")
    assert code == 0
    assert fields["model"] == "opus"
    assert fields["effort"] == "low"
    assert "# model-level: frontier" in raw
    assert body.strip() == "New prompt."
