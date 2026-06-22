# Phase 1 — recommendations 스키마 계약 (Goal Prompt)

> 선행 의존성: **없음** (기반 Phase). 관련 버그: BUG-001, BUG-002.

## 🎯 목표 (Objective)

recommendations 계약을 v1.3 스키마에 **명문화**한다: 고유 ID(REC-NNN), rank/priority 분리, finding_ids 역참조. 신규 필드는 전부 optional로 하위호환 유지.

## 📥 참조 입력 (Inputs)

- `docs/claude-threat-scan-json-schema-v1.3.md` (§15 recommendations, §17 ID Naming Convention)
- `docs/SCHEMA_V1.3_ENFORCEMENT.md` (강제 규칙·체크리스트)
- 결함 근거: `scanreport-20260622143000.json` (priority 정수, finding_ids 부재)

## 🔧 작업 (Tasks)

1. **`docs/claude-threat-scan-json-schema-v1.3.md` §15 recommendations** — `"V1.2와 동일. 변경 없음."` 제거하고 신규 계약 전체 기술:
   - 필드표: `id`(REC-NNN), `rank`(int), `priority`(string), `category`(○), `action`, `rationale`, `finding_ids`(string[]), `affected_files`(○).
   - **명시 규칙**: "priority는 문자열 심각도(Critical/High/Medium/Low)이며 **정수 금지** — 처리 순서는 `rank` 사용." / "finding_ids는 기존 finding ID만 참조, 빈 배열 금지." / "신규 필드(id/rank/finding_ids)는 optional(하위호환)."
   - 예시 JSON 포함.
2. **§17 ID Naming Convention 표**에 행 추가: `recommendations | REC-NNN | REC-001`.
3. **§18 Common Mistakes**에 행 추가: `priority 정수(1~7)` → `priority 문자열 + rank 정수 분리`.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- §15에 `id`/`rank`/`priority`/`finding_ids` 필드표와 "정수 금지" 문구 존재 (`grep "정수 금지"` / `grep "REC-NNN"`).
- §17 ID표에 `REC-NNN` 행 존재.
- 신규 필드가 모두 **optional**로 명시되어 v2.1.0 페이로드가 여전히 유효함을 문서가 보장.
- `SCHEMA_V1.3_ENFORCEMENT.md`에 recommendations 강제 규칙 + 체크리스트 항목 추가 (priority 정수 금지, REC-NNN, finding_ids 기존 참조).

## 🔗 선행 의존성

없음.
