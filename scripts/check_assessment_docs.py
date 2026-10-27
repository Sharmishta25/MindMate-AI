"""Offline documentation checks. Does not read private databases or .env."""
from pathlib import Path
import re
import argparse
import sys
from urllib.parse import unquote
from mindmate.config import PROJECT_ROOT
from mindmate.ai.prompts import VERSION as JOURNAL_VERSION
from mindmate.ai.report_prompts import VERSION as REPORT_VERSION

REQUIRED = ["README.md", "PROMPT_LOG.md", "docs/AI_DESIGN.md", "docs/USER_GUIDE.md",
            "docs/VIDEO_PRESENTATION.md", "docs/DEMO_CHECKLIST.md", "docs/PROJECT_SUMMARY.md",
            "docs/ARCHITECTURE.md", "docs/SECURITY_AND_PRIVACY.md", "docs/AI_AND_MULTILINGUAL.md",
            "docs/SCHEDULER_DEPLOYMENT.md", "docs/DATA_RECOVERY.md", "docs/TEST_REPORT.md", "docs/CHANGELOG.md"]


def check(expected_tests=None):
    issues = []
    files = [PROJECT_ROOT / "README.md", PROJECT_ROOT / "PROMPT_LOG.md"] + sorted((PROJECT_ROOT / "docs").glob("*.md"))
    for relative in REQUIRED:
        path = PROJECT_ROOT / relative
        if not path.is_file() or len(path.read_text(encoding="utf-8").strip()) < 100:
            issues.append(f"Missing or empty required document: {relative}")
    link_count = 0
    for path in files:
        content = path.read_text(encoding="utf-8")
        label = path.relative_to(PROJECT_ROOT).as_posix()
        fences = [line for line in content.splitlines() if line.startswith("```")]
        if len(fences) % 2:
            issues.append(f"Unbalanced code fences: {label}")
        for target in re.findall(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", content):
            if re.match(r"(?:https?://|tel:|mailto:|#)", target):
                continue
            target = unquote(target.split("#", 1)[0].strip("<>"))
            link_count += 1
            if not (path.parent / target).resolve().exists():
                issues.append(f"Broken relative link in {label}: {target}")
        if re.search(r"sk-ant-[A-Za-z0-9_-]{12,}", content):
            issues.append(f"Potential real credential pattern in {label}; inspect without logging its value")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    env_names = set(re.findall(r"^(MINDMATE_\w+)=", example, re.M))
    if any(name not in readme for name in env_names):
        issues.append("README does not cover every example environment variable")
    log = (PROJECT_ROOT / "PROMPT_LOG.md").read_text(encoding="utf-8")
    ids = re.findall(r"^## (\d{3}) -", log, re.M)
    if not ids or sorted(ids) != [f"{i:03d}" for i in range(1, len(ids)+1)] or log.count("### User prompt actually used (verbatim)") != len(ids):
        issues.append("Prompt records must have distinct contiguous IDs and one actual prompt section each")
    design = (PROJECT_ROOT / "docs/AI_DESIGN.md").read_text(encoding="utf-8")
    if JOURNAL_VERSION not in design or REPORT_VERSION not in design:
        issues.append("AI prompt version documentation is stale")
    if expected_tests is not None:
        if type(expected_tests) is not int or expected_tests < 1:
            raise ValueError("Expected test count must be a positive integer")
        for relative in ["README.md", "docs/AI_DESIGN.md", "docs/PROJECT_SUMMARY.md", "docs/SUBMISSION_STATUS.md"]:
            if str(expected_tests) not in (PROJECT_ROOT / relative).read_text(encoding="utf-8"):
                issues.append(f"Expected test evidence not stated in {relative}")
    video = (PROJECT_ROOT / "docs/VIDEO_PRESENTATION.md").read_text(encoding="utf-8")
    try:
        speech = video.split("<!-- SCRIPT_START -->")[1].split("<!-- SCRIPT_END -->")[0]
        words = len(re.findall(r"\b[\w'-]+\b", speech))
        if not 280 <= words <= 390:
            issues.append("Spoken draft outside selected 2-3 minute rehearsal word-count range")
    except IndexError:
        words = 0
        issues.append("Spoken script boundaries missing")
    result = {"required_documents": len(REQUIRED), "reviewed_markdown_files": len(files),
              "relative_links_checked": link_count, "environment_variables": len(env_names),
              "prompt_records": len(ids), "spoken_words": words, "issues": issues}
    print(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-tests", type=int, help="Check an explicitly supplied observed pytest count, not a hardcoded historical count")
    args = parser.parse_args()
    sys.exit(1 if check(args.expected_tests)["issues"] else 0)
