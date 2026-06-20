"""
Tests for tools/validate-spec.sh — runs the real script against fixture
input.md files. Each fixture violates exactly one mandatory K-criterion
(K1/K3/K4/K8), except go.md which satisfies all of them.
"""
import shutil

from helpers import run

JOB_ID = "test-job"


def _make_job_dir(tmp_path, fixture_name, fixtures_dir):
    job_dir = tmp_path / "jobs" / JOB_ID
    job_dir.mkdir(parents=True)
    shutil.copy(fixtures_dir / "validate_spec" / fixture_name, job_dir / "input.md")
    return job_dir


def _run_validate_spec(tmp_path, repo_root):
    return run(["bash", str(repo_root / "tools" / "validate-spec.sh"), JOB_ID], cwd=tmp_path)


def test_go_case_passes_all_criteria(tmp_path, repo_root, fixtures_dir):
    _make_job_dir(tmp_path, "go.md", fixtures_dir)
    result = _run_validate_spec(tmp_path, repo_root)

    assert result.returncode == 0
    assert "MECHANIKUS ELLENŐRZÉS: GO" in result.stdout
    assert "FAIL:" not in result.stdout


def test_k1_violation_missing_source_path(tmp_path, repo_root, fixtures_dir):
    _make_job_dir(tmp_path, "k1_violation.md", fixtures_dir)
    result = _run_validate_spec(tmp_path, repo_root)

    assert result.returncode == 1
    assert "MECHANIKUS ELLENŐRZÉS: NO-GO" in result.stdout
    assert "FAIL: K1:" in result.stdout
    assert "FAIL: K3:" not in result.stdout
    assert "FAIL: K4:" not in result.stdout
    assert "FAIL: K8:" not in result.stdout


def test_k3_violation_missing_forbidden_shortcut(tmp_path, repo_root, fixtures_dir):
    _make_job_dir(tmp_path, "k3_violation.md", fixtures_dir)
    result = _run_validate_spec(tmp_path, repo_root)

    assert result.returncode == 1
    assert "MECHANIKUS ELLENŐRZÉS: NO-GO" in result.stdout
    assert "FAIL: K3:" in result.stdout
    assert "FAIL: K1:" not in result.stdout
    assert "FAIL: K4:" not in result.stdout
    assert "FAIL: K8:" not in result.stdout


def test_k4_violation_missing_output_filename(tmp_path, repo_root, fixtures_dir):
    _make_job_dir(tmp_path, "k4_violation.md", fixtures_dir)
    result = _run_validate_spec(tmp_path, repo_root)

    assert result.returncode == 1
    assert "MECHANIKUS ELLENŐRZÉS: NO-GO" in result.stdout
    assert "FAIL: K4:" in result.stdout
    assert "FAIL: K1:" not in result.stdout
    assert "FAIL: K3:" not in result.stdout
    assert "FAIL: K8:" not in result.stdout


def test_k8_violation_missing_claim_evidence_table(tmp_path, repo_root, fixtures_dir):
    _make_job_dir(tmp_path, "k8_violation.md", fixtures_dir)
    result = _run_validate_spec(tmp_path, repo_root)

    assert result.returncode == 1
    assert "MECHANIKUS ELLENŐRZÉS: NO-GO" in result.stdout
    assert "FAIL: K8:" in result.stdout
    assert "FAIL: K1:" not in result.stdout
    assert "FAIL: K3:" not in result.stdout
    assert "FAIL: K4:" not in result.stdout


def test_missing_input_md_is_no_go(tmp_path, repo_root):
    (tmp_path / "jobs" / JOB_ID).mkdir(parents=True)
    result = _run_validate_spec(tmp_path, repo_root)

    assert result.returncode == 1
    assert "NO-GO" in result.stderr


def test_missing_job_id_argument_usage_error(repo_root, tmp_path):
    result = run(["bash", str(repo_root / "tools" / "validate-spec.sh")], cwd=tmp_path)

    assert result.returncode == 1
    assert "Usage:" in result.stderr
