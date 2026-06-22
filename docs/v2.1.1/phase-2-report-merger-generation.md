# Phase 2 — report-merger 생성 + 번역 + 사전 (Goal Prompt)

> 선행 의존성: **Phase 1**. 관련 버그: BUG-001, BUG-002.

## 🎯 목표 (Objective)

report-merger가 신규 recommendations 계약대로 권장조치를 **생성**하도록 지시문을 갱신하고, bilingual-translator의 번역 비대상 필드를 명시하며, 뷰어 라벨용 사전 키를 추가한다.

## 📥 참조 입력 (Inputs)

- `skills/report-merger/SKILL.md` (ID 할당 규칙표 L91-106, 권장사항 생성 L155-173)
- `skills/bilingual-translator/SKILL.md` (번역 규칙)
- `dictionary/security-terms-en-ko.json`, `dictionary/translation-rules-ko.json`
- Phase 1 산출 §15 계약

## 🔧 작업 (Tasks)

1. **`skills/report-merger/SKILL.md`**:
   - "ID 할당 규칙" 표에 `recommendations | REC-NNN | REC-001` 행 추가.
   - "권장사항 생성" 구조를 신규 계약(id/rank/priority/finding_ids)으로 교체.
   - **산정 규칙 명문화**: `priority` = 참조 finding들의 최고 severity / `rank` = priority 내림차순 정렬 순번(1=최우선) / `finding_ids` = 근거 finding ID(최소 1개, 기존 ID만) / `priority`는 문자열·정수 금지.
   - 검증 체크리스트에 항목 추가(REC-NNN, finding_ids 비어있지 않음, priority 문자열).
2. **`skills/bilingual-translator/SKILL.md`**: recommendations 처리 시 `id`/`rank`/`finding_ids`는 **구조 필드(번역 비대상)**, `priority`는 severity처럼 등급 번역(Critical→심각), `action`/`rationale`/`category`는 번역임을 명시.
3. **`skills/threat-scan-orchestrator/SKILL.md`**: recommendations 예시가 `[]` 뿐이면 변경 불요 — 확인만.
4. **사전 (뷰어 라벨용)**: `dictionary/security-terms-en-ko.json` 또는 `translation-rules-ko.json`에 `rank`→"순위", `relatedFindings`→"관련 발견" 매핑 추가(뷰어 `t()`와 정합).

## ✅ 완료 조건 (Acceptance) — 검증 가능

- report-merger SKILL.md ID표에 `REC-NNN` 행 존재 (`grep REC-NNN`).
- "권장사항 생성"에 priority=최고 severity / rank=정렬 순번 / finding_ids=근거 규칙이 문장으로 존재.
- bilingual-translator에 "id/rank/finding_ids 번역 비대상" 문구 존재.
- 사전에 rank/relatedFindings EN-KO 키 존재.

## 🔗 선행 의존성

Phase 1 (스키마 계약 확정).
