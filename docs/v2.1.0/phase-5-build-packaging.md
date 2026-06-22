# Phase 5 — 빌드 & 패키징 (Goal Prompt)

> 선행 의존성: **Phase 1–4**

## 🎯 목표 (Objective)

신규 스킬·레지스트리·v1.3 스키마를 Claude Desktop 배포 패키지에 포함하고 `threat-scan-security.zip` 을 재생성한다. VERSION을 2.1.0으로 올린다.

## 📥 참조 입력 (Inputs)

- `build_claude_desktop.sh` (sub-skills/docs/dictionary 복사 + zip)
- `VERSION` (현재 2.0.0)
- Phase 2/3 신규 스킬, `dictionary/model-capabilities.json`, Phase 1 v1.3 docs

## 🔧 작업 (Tasks)

1. `build_claude_desktop.sh` 갱신:
   - sub-skills 복사 목록에 `relationship-graph-analyzer`, `model-validity-analyzer` 추가.
   - dictionary 복사에 `model-capabilities.json` 포함.
   - docs 복사에 `claude-threat-scan-json-schema-v1.3.md`, `SCHEMA_V1.3_ENFORCEMENT.md` 추가(v1.2도 유지 가능).
   - 통합 SKILL.md(오케스트레이터 머지)에 신규 Phase 4.5/4.6 반영.
2. `VERSION` → `2.1.0`.
3. `threat-scan-security.zip`(+`dist_claude_desktop/`) 재생성.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- 빌드 산출물 `references/sub-skills/` 에 신규 스킬 2종 포함.
- `references/dictionary/` 에 `model-capabilities.json` 포함.
- `references/docs/` 에 v1.3 스키마/enforcement 포함.
- 패키지 레이아웃이 기존(references/ 구조)과 동일.
- `VERSION` == 2.1.0, zip 재생성됨.

## 🔗 선행 의존성

Phase 1–4.
