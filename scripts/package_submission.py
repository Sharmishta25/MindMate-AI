"""Allowlisted source-only archive; never includes databases, .env or caches."""
from pathlib import Path
import hashlib
import zipfile
from mindmate.config import PROJECT_ROOT

OUTPUT = PROJECT_ROOT / "output/submission"
DOC_NAMES = (
    "AI_DESIGN.md", "ARCHITECTURE.md", "DEMO_CHECKLIST.md", "DOCUMENTATION_CHECK.md",
    "PROJECT_SUMMARY.md", "QA_REPORT.md", "SAFETY_AND_PRIVACY.md", "SUBMISSION_STATUS.md",
    "USER_GUIDE.md", "VIDEO_PRESENTATION.md", "DEPLOYMENT.md", "RELEASE_AUDIT.md", "RELEASE_CHECKLIST.md",
    "FEATURE_EXPANSION.md", "SECURITY_AND_PRIVACY.md", "AI_AND_MULTILINGUAL.md", "SCHEDULER_DEPLOYMENT.md", "DATA_RECOVERY.md", "TEST_REPORT.md", "CHANGELOG.md",
)


def source_files():
    root_names = ["README.md", "PROMPT_LOG.md", "app.py", ".env.example", ".gitignore", "pytest.ini",
                  "requirements.txt", "requirements-dev.txt", "requirements-lock.txt", ".streamlit/config.toml"]
    paths = [PROJECT_ROOT / name for name in root_names]
    paths.extend(PROJECT_ROOT / "mindmate/i18n" / (code+".json") for code in ("en","hi","mr"))
    for folder in ("mindmate", "tests", "scripts"):
        paths.extend((PROJECT_ROOT / folder).rglob("*.py"))
    paths.extend(PROJECT_ROOT / "docs" / name for name in DOC_NAMES)
    paths = sorted(set(paths))
    for path in paths:
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(PROJECT_ROOT):
            raise ValueError("Source path is missing, linked or escapes the project")
        if path.resolve() != path.absolute():
            raise ValueError("Source aliases/junctions are not included in release archives")
        # Reject binary files disguised with source extensions before packaging.
        content = path.read_text(encoding="utf-8-sig")
        if path.suffix == ".py":
            import ast
            ast.parse(content, filename=str(path))
    return paths


def package():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    paths = source_files()
    archive = OUTPUT / "MindMate-AI-source.zip"
    temporary = OUTPUT / "MindMate-AI-source.zip.tmp"
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in paths:
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            bundle.write(path, "MindMate-AI/" + relative)
    with zipfile.ZipFile(temporary) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Archive CRC verification failed")
        for info in bundle.infolist():
            relative = info.filename.removeprefix("MindMate-AI/")
            parts = Path(relative).parts
            if any(part in {".venv", "data", "tmp", "private", "exports", "__pycache__", ".git"} for part in parts) or Path(relative).name == ".env":
                raise ValueError("Private/runtime path found in source archive")
            if Path(relative).suffix in {".db", ".sqlite", ".sqlite3", ".pyc"}:
                raise ValueError("Database/cache file found in source archive")
            if bundle.read(info) != (PROJECT_ROOT / relative).read_bytes():
                raise ValueError("Archive content differs from source")
    temporary.replace(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (OUTPUT / "SHA256SUMS.txt").write_text(digest + "  MindMate-AI-source.zip\n", encoding="utf-8")
    (OUTPUT / "SOURCE_MANIFEST.txt").write_text("\n".join(p.relative_to(PROJECT_ROOT).as_posix() for p in paths) + "\n", encoding="utf-8")
    print(f"Packaged {len(paths)} source/document files; CRC and byte comparison passed.")
    print(f"SHA-256: {digest}")
    return archive


if __name__ == "__main__":
    package()
