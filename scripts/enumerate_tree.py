#!/usr/bin/env python3
"""
enumerate_tree.py — 결정론 파일 열거기 (stdlib-only, v2.5.1 / D1).

단계 0(소스 준비, 셸 허용)에서 실행해 대상 트리를 완전 열거하고,
repository_summary.file_statistics 정본 포맷을 직접 산출한다(LLM 산수 제거).
Desktop(파일 열거 도구 부재)과 Code(Glob 커버리지 검증 보조) 양 모드가 공유한다.

사용법:
  python3 enumerate_tree.py <target_dir> [--out file-manifest.json] [--json]

산출: file_statistics(항목 합 + other == total_files 정합 보장), files, code_files,
      sensitive_candidates, manifest_files, ai_agent_paths.
외부 의존·네트워크 없음. 동일 입력 → 동일 출력.
"""
import argparse
import json
import os
import sys

EXCLUDE_DIRS = {"node_modules", ".git", ".next", "dist", "build", "vendor",
                "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache",
                "dist_claude_desktop"}

# 확장자 → file_statistics 카테고리 (리포트 정본 키와 일치)
EXT_CATEGORY = {
    ".py": "python_files",
    ".ts": "typescript_tsx", ".tsx": "typescript_tsx",
    ".js": "javascript_files", ".jsx": "javascript_files", ".mjs": "javascript_files", ".cjs": "javascript_files",
    ".md": "markdown_files", ".markdown": "markdown_files",
    ".json": "json_files", ".jsonc": "json_files",
    ".html": "html_files", ".htm": "html_files",
    ".css": "css_files", ".scss": "css_files", ".sass": "css_files",
    ".yaml": "yaml_files", ".yml": "yaml_files",
    ".sh": "shell_scripts", ".bash": "shell_scripts", ".zsh": "shell_scripts",
    ".ps1": "powershell_files", ".psm1": "powershell_files",
    ".txt": "text_files",
    ".toml": "configuration_files", ".ini": "configuration_files",
    ".cfg": "configuration_files", ".conf": "configuration_files",
    ".pem": "pem_files",
    ".key": "key_files",
}
# 통계 키 표시 순서(0으로라도 포함해 안정적 출력)
STAT_KEYS = [
    "total_files", "python_files", "typescript_tsx", "javascript_files",
    "markdown_files", "json_files", "html_files", "css_files", "yaml_files",
    "shell_scripts", "powershell_files", "text_files", "configuration_files",
    "env_files", "pem_files", "key_files", "gitignore_gitkeep", "other",
]
CODE_CATEGORIES = {"python_files", "typescript_tsx", "javascript_files",
                   "shell_scripts", "powershell_files"}

# 코드 파일 확장자(code_files 목록용)
CODE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
             ".go", ".rb", ".java", ".php", ".rs", ".c", ".cpp", ".cc",
             ".cs", ".sh", ".bash", ".zsh", ".ps1", ".kt", ".swift", ".scala"}

# AI 에이전트 구성요소 (오케스트레이터 Phase 0(d)와 동일 목록)
AI_DIR_NAMES = {".claude", ".cursor", ".codex", ".gemini", "agents", "prompts"}
AI_FILE_NAMES = {"AGENTS.md", "SKILL.md", ".mcp.json", "mcp.json",
                 "copilot-instructions.md"}

# 의존성 매니페스트/lock
MANIFEST_NAMES = {
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements.txt", "requirements-lock.txt", "pyproject.toml",
    "poetry.lock", "Pipfile", "Pipfile.lock",
    "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
    "pom.xml", "build.gradle", "Gemfile", "Gemfile.lock",
    "composer.json", "composer.lock",
}
# 민감 후보 파일명 키워드
SENSITIVE_KEYWORDS = ("secret", "credential", "password", "token", "private")


def categorize(fname):
    low = fname.lower()
    if low.startswith(".env"):
        return "env_files"
    if fname in (".gitignore", ".gitkeep", ".gitattributes"):
        return "gitignore_gitkeep"
    _, ext = os.path.splitext(fname)
    return EXT_CATEGORY.get(ext.lower(), "other")


def is_sensitive(fname):
    low = fname.lower()
    if low.startswith(".env"):
        return True
    _, ext = os.path.splitext(low)
    if ext in (".pem", ".key", ".p12", ".pfx", ".keystore"):
        return True
    return any(k in low for k in SENSITIVE_KEYWORDS)


def main(argv=None):
    p = argparse.ArgumentParser(description="Deterministic file-tree enumerator (v2.5.1 D1)")
    p.add_argument("target", help="스캔 대상 디렉터리")
    p.add_argument("--out", default=None, help="manifest JSON 출력 경로 (기본 stdout 요약)")
    p.add_argument("--json", action="store_true", help="전체 manifest를 stdout에 JSON으로 출력")
    args = p.parse_args(argv)

    root = os.path.abspath(args.target)
    if not os.path.isdir(root):
        print("[ERROR] not a directory: %s" % root, file=sys.stderr)
        return 1

    stats = {k: 0 for k in STAT_KEYS}
    files, code_files, sensitive, manifests, ai_paths = [], [], [], [], []

    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
        rel_dir = os.path.relpath(dp, root)
        # AI 구성요소 디렉터리
        for d in list(dns):
            if d in AI_DIR_NAMES:
                ai_paths.append((os.path.join(rel_dir, d) if rel_dir != "." else d) + "/")
        for fn in fns:
            rel = os.path.join(rel_dir, fn) if rel_dir != "." else fn
            rel = rel.replace(os.sep, "/")
            files.append(rel)
            stats["total_files"] += 1
            cat = categorize(fn)
            stats[cat] = stats.get(cat, 0) + 1
            _, ext = os.path.splitext(fn.lower())
            if ext in CODE_EXTS:
                code_files.append(rel)
            if is_sensitive(fn):
                sensitive.append(rel)
            if fn in MANIFEST_NAMES:
                manifests.append(rel)
            if fn in AI_FILE_NAMES:
                ai_paths.append(rel)

    # 정합 보장: 분류 항목 합(total 제외) + 미분류는 이미 other로 흘렀으므로 재계산 검증
    counted = sum(v for k, v in stats.items() if k not in ("total_files", "other"))
    stats["other"] = stats["total_files"] - counted
    if stats["other"] < 0:
        # 이론상 불가(카테고리 중복 없음) — 방어적 보정
        stats["other"] = 0

    manifest = {
        "target": root,
        "file_statistics": {k: stats[k] for k in STAT_KEYS},
        "files": sorted(files),
        "code_files": sorted(code_files),
        "sensitive_candidates": sorted(set(sensitive)),
        "manifest_files": sorted(set(manifests)),
        "ai_agent_paths": sorted(set(ai_paths)),
    }

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        fs = manifest["file_statistics"]
        print("[OK] enumerate_tree: %d files (code=%d, sensitive=%d, manifests=%d, ai_paths=%d)"
              % (fs["total_files"], len(code_files), len(manifest["sensitive_candidates"]),
                 len(manifest["manifest_files"]), len(manifest["ai_agent_paths"])))
        # 정합 자기검증 출력
        chk = sum(v for k, v in fs.items() if k not in ("total_files",))
        print("[STAT] sum(categories incl. other)=%d, total_files=%d, consistent=%s"
              % (chk, fs["total_files"], chk == fs["total_files"]))
        if manifest["ai_agent_paths"]:
            print("[AI] " + ", ".join(manifest["ai_agent_paths"][:10]))
        if args.out:
            print("[OUT] " + args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
