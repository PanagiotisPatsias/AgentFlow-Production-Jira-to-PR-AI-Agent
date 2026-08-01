from agentflow.tools.verification.runner import VerificationRunner


def test_detects_nested_python_project_root(tmp_path) -> None:
    repository = tmp_path / "repository"
    project = repository / "Intellishore"
    tests = project / "tests"
    tests.mkdir(parents=True)
    (repository / ".git").mkdir()
    (project / "pyproject.toml").write_text(
        "[project]\nname = 'example'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    (tests / "test_feature.py").write_text(
        "def test_feature():\n    assert True\n",
        encoding="utf-8",
    )
    scripts = repository / "scripts"
    scripts.mkdir()
    (scripts / "test_unrelated.py").write_text(
        "raise RuntimeError('must not be collected')\n",
        encoding="utf-8",
    )

    detected = VerificationRunner._detect_project_root(repository)

    assert detected == project
