"""Synthetic release-tool regressions; do not read private databases or keys."""
from pathlib import Path
import hashlib
import zipfile
import pytest
from scripts import package_submission as release


@pytest.fixture
def release_tree(tmp_path, monkeypatch):
    root = tmp_path / "source"
    root.mkdir()
    monkeypatch.setattr(release, "PROJECT_ROOT", root)
    monkeypatch.setattr(release, "OUTPUT", tmp_path / "package")
    fixed = ["README.md", "PROMPT_LOG.md", "app.py", ".env.example", ".gitignore", "pytest.ini", "requirements.txt", "requirements-dev.txt", "requirements-lock.txt", ".streamlit/config.toml"]
    fixed += ["docs/" + name for name in release.DOC_NAMES]
    fixed += ["mindmate/i18n/"+code+".json" for code in ("en","hi","mr")]
    for name in fixed:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pass\n" if path.suffix == ".py" else "Synthetic fixture\n", encoding="utf-8")
    return root


def test_private_and_unreviewed_files_are_not_packaged(release_tree):
    for name in [".env", "docs/personal-notes.md", "data/mindmate.sqlite3", "tmp/demo.sqlite3", "private/journal.txt"]:
        path = release_tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Synthetic private fixture", encoding="utf-8")
    archive = release.package()
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        assert "MindMate-AI/.env.example" in names
        assert not any(x in name for name in names for x in ["personal-notes", ".sqlite3", "private/"])
        assert "MindMate-AI/.env" not in names
        assert bundle.testzip() is None
    assert hashlib.sha256(archive.read_bytes()).hexdigest() in (release.OUTPUT / "SHA256SUMS.txt").read_text()


def test_missing_reviewed_document_blocks_package(release_tree):
    (release_tree / "docs/RELEASE_CHECKLIST.md").unlink()
    with pytest.raises(ValueError, match="missing"):
        release.source_files()


def test_binary_disguised_as_python_is_rejected(release_tree):
    (release_tree / "app.py").write_bytes(b"\xff\x00synthetic binary")
    with pytest.raises(UnicodeError):
        release.source_files()


def test_source_alias_is_rejected(release_tree, monkeypatch):
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == "app.py" or original(self))
    with pytest.raises(ValueError, match="linked"):
        release.source_files()
