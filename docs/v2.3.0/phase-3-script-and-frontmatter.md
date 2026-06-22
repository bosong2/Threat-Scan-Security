# Phase 3 — 스크립트 경로 확장 + SKILL.md frontmatter

## 목표

① 생성기 스크립트가 플러그인 환경 경로를 해석하게 하고, ② 오케스트레이터 스킬을 Claude Code 오케스트레이션 본체로 승격하며, ③ Desktop계열 SKILL.md를 유효한 Claude Code 스킬로 만든다 — **본문 불변**.

## 변경 1 — `scripts/generate_html_report.py`

`resolve_template()`의 후보 경로 목록에 `CLAUDE_PLUGIN_ROOT` 기반 경로를 **최우선**으로 추가.

```python
candidates = []
plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
if plugin_root:
    candidates.append(os.path.join(plugin_root, "dictionary", fname))
candidates += [
    os.path.join(_SCRIPT_DIR, "..", "dictionary", fname),       # repo
    os.path.join(_SCRIPT_DIR, "..", "..", "dictionary", fname), # dist(references)
    os.path.join(_SCRIPT_DIR, fname),
]
```

- 기존 repo/dist 후보는 그대로 유지(회귀 없음).
- env 미설정 시 동작 변화 없음.

## 변경 2 — `skills/threat-scan-orchestrator/SKILL.md` (frontmatter + 오케스트레이션)

frontmatter 추가:

```yaml
---
name: threat-scan-orchestrator
description: >
  Orchestrate the full Claude Threat Scan pipeline (단계 0–11) over a target
  skill/agent/plugin/repo and produce a bilingual JSON report plus a KO HTML
  report. Use when asked to scan, audit, or vet a repository for security.
allowed-tools: Agent(tss-source-handler), Agent(tss-repo-indexer), Agent(tss-static-analyzer), Agent(tss-binary-analyzer), Agent(tss-skill-analyzer), Agent(tss-relationship-graph), Agent(tss-model-validity), Agent(tss-sensitive-patterns), Agent(tss-policy-verifier), Agent(tss-prompt-optimizer), Agent(tss-sbom), Agent(tss-deepdive), Agent(tss-report-merger), Agent(tss-translator), Agent(tss-html-report), Bash, Read
---
```

본문: 기존 스캔 순서표(단계 0–11)·제약·스키마 절은 **보존**. Claude Code 실행 시 각 단계에서 대응 `tss-*` 에이전트를 Agent 도구로 호출하라는 매핑 문단을 추가(Desktop의 `@skill` 호출과 병기 — 모드별 해석).

> Desktop 빌드(`build_claude_desktop.sh`)는 `ORCH_BODY=$(cat .../threat-scan-orchestrator/SKILL.md)`로 본문을 읽어 자체 SKILL.md를 합성한다. frontmatter가 본문 앞에 붙어도 Desktop SKILL.md 합성에는 텍스트로 포함될 뿐 동작 비파괴 — Phase 4/5에서 회귀 확인.

## 변경 3 — Desktop계열 13개 SKILL.md frontmatter 추가

frontmatter 없는 13개(`source-handler`, `repo-indexer`, `static-code-analyzer`, `binary-analyzer`, `skill-security-analyzer`, `relationship-graph-analyzer`, `model-validity-analyzer`, `sensitive-pattern-matcher`, `agent-policy-verifier`, `prompt-optimizer`, `report-merger`, `bilingual-translator`, `html-report-generator`)에 최소 frontmatter 추가:

```yaml
---
name: <dir-name>
description: <기존 "## 개요" 1문장 요약>
---
```

- **본문(`## 개요` 이하) 완전 불변** — 에이전트가 참조하는 단일 원천이므로 내용 변경 금지.
- `securityreports-*` 5개는 이미 frontmatter 보유 → Phase 4에서 deprecated 표기만.

## 완료 조건 (검증 가능)

- [ ] `generate_html_report.py`에 `CLAUDE_PLUGIN_ROOT` 후보 추가, `py_compile` 통과, repo·dist 기존 경로 회귀 없음.
- [ ] `threat-scan-orchestrator/SKILL.md`에 `allowed-tools: Agent(tss-...)` 15개 + Bash/Read, 기존 본문(스캔 순서표·제약) 보존.
- [ ] frontmatter 없던 13개 SKILL.md 모두 frontmatter 보유, `## 개요` 이하 본문 불변.

## 검증

```bash
cd Threat-scan-security
python3 -m py_compile scripts/generate_html_report.py && echo "compile OK"
grep -c "CLAUDE_PLUGIN_ROOT" scripts/generate_html_report.py    # ≥ 1
grep -q "allowed-tools:.*tss-html-report" skills/threat-scan-orchestrator/SKILL.md && echo "orch OK"
# 전 스킬 frontmatter 보유 확인
miss=0; for f in skills/*/SKILL.md; do [ "$(head -1 "$f")" = "---" ] || { echo "NO FM: $f"; miss=1; }; done; [ $miss -eq 0 ] && echo "ALL FM OK"
```
