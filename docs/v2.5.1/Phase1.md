# Phase 1 — 결정론 파일 열거: `enumerate_tree.py` + 단계 0 배선 (D1)

## 목표

Desktop의 파일 열거 도구 부재(커버리지 붕괴·file_statistics 자기모순의 원인)를, 기존 셸 허용
단계 0에서 실행하는 결정론 Python 스크립트로 해소한다. Code 모드도 동일 manifest를 커버리지
정본으로 공유한다.

## 1-A. `scripts/enumerate_tree.py` (신규 — stdlib-only, 결정론)

CLI: `python3 scripts/enumerate_tree.py <target_dir> [--out file-manifest.json] [--json]`

산출 (`file-manifest.json`):

```json
{
  "target": "/abs/path",
  "file_statistics": {            // repository_summary 정본 포맷 그대로
    "total_files": 166, "python_files": 36, "typescript_tsx": 42,
    "javascript_files": 2, "markdown_files": 49, "json_files": 9,
    "html_files": 1, "css_files": 1, "yaml_files": 3, "shell_scripts": 9,
    "env_files": 2, "pem_files": 0, "key_files": 0, "other": 12
  },
  "files": ["backend/app/main.py", "..."],          // 제외 규칙 적용 후 전체 상대경로
  "code_files": ["...
"],                              // 코드 확장자 서브셋
  "sensitive_candidates": [".env", "docs/x.md"],     // .env*·*.pem·*.key·credential 키워드 파일명
  "manifest_files": ["backend/requirements.txt", "backend/requirements-lock.txt", "frontend/package.json", "frontend/package-lock.json"],
  "ai_agent_paths": [".claude/", "playbooks/", "AGENTS.md"]   // Phase 0(d) 게이트와 동일 규칙
}
```

규칙:
- 제외 디렉터리: `node_modules`, `.git`, `.next`, `dist`, `build`, `vendor`, `__pycache__`, `.venv`.
- `file_statistics` 항목 합계 + `other` = `total_files` **정합 보장**(스크립트가 계산 — LLM 산수 금지).
- AI 구성요소 탐지 규칙은 오케스트레이터 Phase 0(d)의 `os.walk` 스니펫과 **동일 목록** 사용
  (디렉터리 `.claude/.cursor/.codex/.gemini/agents/prompts`, 파일 `AGENTS.md/SKILL.md/.mcp.json/mcp.json/copilot-instructions.md`).
- 외부 의존·네트워크 없음. 동일 입력 → 동일 출력.

## 1-B. Desktop 배선 (`skills/threat-scan-orchestrator/SKILL.md` — Desktop 섹션 + 공유부)

Desktop 실행 절차에 단계 0 확장 명시:

1. 소스 준비(압축 해제/복사) 직후 실행:
   `python3 references/scripts/enumerate_tree.py <target> --out file-manifest.json`
2. **소비 계약**:
   - 단계 1(repo-indexer): manifest의 `file_statistics`를 **수정 없이 그대로** `repository_summary.file_statistics`에 사용. `sensitive_candidates`·`manifest_files`를 출발점으로 검토.
   - 단계 2–8: `files`/`code_files` 목록을 커버리지 기준으로 사용 — "**목록에 있는 파일만, 그리고 전부**" 분석. 경로 추측 금지.
   - AI 구성요소 게이트(기존 Desktop 대화 질의): `ai_agent_paths`를 탐지 결과로 사용(중복 탐색 제거).
3. BUG-02 준수: Desktop 섹션 서술에 Code 전용 명칭 금지.

## 1-C. Code 배선 (Code 섹션)

- Phase 0(a) 소스 준비 직후(또는 0(c) 루트 해석 후) 동일 스크립트 실행:
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/enumerate_tree.py" <RESOLVED_TARGET_ROOT> --out <SCAN_TMP>/file-manifest.json`
- 워커 프롬프트에 manifest 경로 전달 — `_meta.files_total`은 manifest의 `total_files`를 정본으로 사용
  (Glob 열거와 병행: Glob은 탐색용, manifest는 검증 정본).
- Phase 0(d) 게이트는 manifest의 `ai_agent_paths` 재사용 가능(기존 스니펫은 폴백 유지).

## 완료 조건 (검증 가능)

- [ ] `python3 scripts/enumerate_tree.py . --out /tmp/m.json` (이 repo 대상) 성공,
      `file_statistics` 항목 합+other = total_files 정합 (python 검증 스니펫으로 확인).
- [ ] `ai_agent_paths`가 Phase 0(d) 스니펫 실행 결과와 동일 집합.
- [ ] Desktop 섹션·Code 섹션에 실행+소비 계약 명문화, Desktop 섹션 Code 명칭 오염 0.
- [ ] `bash build_claude_desktop.sh` 후 dist `references/scripts/enumerate_tree.py` 존재.
