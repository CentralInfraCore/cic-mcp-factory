"""
Tests for tools/run-job.sh — limited to the network-free, agent-free subset:
argument validation and the validate-spec.sh NO-GO short-circuit (both before
any git clone / `claude --print` invocation). Real git clone, push and
`claude --print` calls are explicitly NOT exercised here — see the test
suite report's Risks section.
"""
import os
import shutil

from helpers import run


def _setup_workdir(tmp_path, repo_root, fixture_name, fixtures_dir):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    shutil.copy(repo_root / "tools" / "run-job.sh", tools_dir / "run-job.sh")
    shutil.copy(repo_root / "tools" / "validate-spec.sh", tools_dir / "validate-spec.sh")
    shutil.copytree(fixtures_dir / "run_job" / fixture_name, tmp_path / "jobs" / fixture_name)
    return tmp_path


def _fake_home_with_agent(tmp_path, agent_id):
    home = tmp_path / "fake-home"
    agent_dir = home / ".claude-personal" / "agents" / agent_id
    agent_dir.mkdir(parents=True)
    return home


def test_missing_job_id_argument_is_usage_error(repo_root, tmp_path):
    result = run(["bash", str(repo_root / "tools" / "run-job.sh")], cwd=tmp_path)

    assert result.returncode != 0
    assert "Adj meg egy job-id-t" in result.stderr


def test_no_go_spec_short_circuits_before_agent_start(tmp_path, repo_root, fixtures_dir):
    workdir = _setup_workdir(tmp_path, repo_root, "no-go-job", fixtures_dir)
    home = _fake_home_with_agent(tmp_path, "test-agent")
    env = {**os.environ, "HOME": str(home)}

    result = run(
        ["bash", "tools/run-job.sh", "no-go-job", "test-agent"],
        cwd=workdir,
        env=env,
    )

    assert result.returncode == 1
    assert "validate-spec.sh NO-GO" in result.stdout
    assert "MECHANIKUS ELLENŐRZÉS: NO-GO" in result.stdout
    # must not have progressed to the running-state commit/clone stage
    assert "running (" not in result.stdout
    assert not (workdir / "jobs" / "index.yaml").exists()
    assert not (workdir / "jobs" / "no-go-job" / "workspace").exists()


def test_resume_flag_routes_to_session_id_check_not_validate_spec(tmp_path, repo_root, fixtures_dir):
    workdir = _setup_workdir(tmp_path, repo_root, "resume-no-session", fixtures_dir)
    home = _fake_home_with_agent(tmp_path, "test-agent")
    env = {**os.environ, "HOME": str(home)}

    result = run(
        ["bash", "tools/run-job.sh", "resume-no-session", "test-agent", "--resume"],
        cwd=workdir,
        env=env,
    )

    assert result.returncode == 1
    assert "meta.yaml agent.session_id üres" in result.stdout
    # proves --resume was parsed as RESUME=1: validate-spec.sh (the non-resume
    # path) must NOT have run, even though the fixture input.md would NO-GO it
    assert "validate-spec" not in result.stdout
    assert not (workdir / "jobs" / "index.yaml").exists()
