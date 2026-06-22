# Phase 2 — 커맨드 계층 (`commands/threat-scan*.md`)

## 목표

Claude Code 사용자 진입점인 슬래시 커맨드를 추가한다. SkillScan(`commands/skillscan*.md`) 형식을 따른다.

## 커맨드 정의

### `commands/threat-scan.md` — 전체 스캔

```markdown
---
description: Run a full Threat-scan security audit and emit JSON + KO HTML report
argument-hint: <path-or-git-url-or-zip>
---

Run a full Claude Threat Scan on: **$ARGUMENTS**

Use the `threat-scan-orchestrator` skill to drive the pipeline (단계 0–11).
별도 요구가 없으면 **bilingual JSON 리포트와 KO HTML 리포트를 함께 산출**한다.
산출 파일 경로(JSON·HTML)와 그래프 verdict 요약을 사용자에게 보고한다.
```

- 기본 동작: JSON(`scanreport-YYYYMMDDhhmmss.json`) + KO HTML 둘 다 출력 — GOAL의 기본 동작 계승.
- 인자: 로컬 경로 / GitHub URL / `owner/repo` / ZIP (source-handler가 감지).

### `commands/threat-scan-html.md` — 기존 JSON → HTML 재생성

```markdown
---
description: Generate a static HTML report from an existing Threat-scan JSON
argument-hint: <report.json> [ko|en]
---

기존 bilingual JSON 리포트(**$ARGUMENTS**)로부터 정적 HTML 리포트를 생성한다.
`tss-html-report` 에이전트(또는 직접 Bash)로:
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate_html_report.py" <report.json> --lang <ko|en>
산출 HTML 경로를 보고한다. LLM 추론 없이 결정론적 파일 처리.
```

- 언어 인자 생략 시 `ko`.
- 전체 재스캔 없이 HTML만 다시 뽑는 경량 경로.

### `commands/threat-scan-help.md` — 안내

```markdown
---
description: Show Threat-scan usage, pipeline steps, and verdict meanings
---
```

본문에 포함:
- 사용법: `/threat-scan <target>`, `/threat-scan-html <json> [ko|en]`.
- 파이프라인 단계 0–11 요약표.
- verdict 의미: `INSTALL_OK` · `REVIEW` · `DISABLE` · `REMOVE`.
- model_effectiveness: `VALID` · `DEGRADED` · `OBSOLETE` · `MODEL_LOCKED`.
- 최종 판정 분류: `Confirmed` · `Mitigated` · `False Positive`.
- **레거시 안내**: 구 `/securityreports-*`는 deprecated → `/threat-scan` 사용 권장.

## 완료 조건 (검증 가능)

- [ ] `commands/threat-scan.md`·`threat-scan-html.md`·`threat-scan-help.md` 존재.
- [ ] 각 커맨드 frontmatter에 `description` 존재, 스캔/HTML 커맨드에 `argument-hint` 존재.
- [ ] `threat-scan.md`가 `threat-scan-orchestrator` 스킬을 호출하고 기본 JSON+KO HTML 산출을 명시.
- [ ] `threat-scan-html.md`가 `generate_html_report.py` 호출 경로 포함.
- [ ] `threat-scan-help.md`에 레거시 deprecated 안내 포함.

## 검증

```bash
cd Threat-scan-security
ls commands/threat-scan*.md                      # → 3개
grep -q "threat-scan-orchestrator" commands/threat-scan.md && echo OK
grep -q "generate_html_report.py" commands/threat-scan-html.md && echo OK
grep -q "deprecated\|securityreports" commands/threat-scan-help.md && echo OK
```
