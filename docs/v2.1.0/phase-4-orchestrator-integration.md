# Phase 4 — 오케스트레이터 통합 (Goal Prompt)

> 선행 의존성: **Phase 2, 3**

## 🎯 목표 (Objective)

신규 스킬 2종을 오케스트레이터 파이프라인에 편입하고, 최종 리포트가 그래프 verdict·컴포넌트 verdict·모델 효과성을 포함하도록 한다. 이중언어 처리까지 일관되게.

## 📥 참조 입력 (Inputs)

- `skills/threat-scan-orchestrator/SKILL.md` (파이프라인 Phase 0–10)
- `skills/report-merger/SKILL.md` (영문 리포트 병합)
- `skills/bilingual-translator/SKILL.md` (EN→KO)
- Phase 2 `relationship-graph-analyzer`, Phase 3 `model-validity-analyzer`
- Phase 1 v1.3 스키마

## 🔧 작업 (Tasks)

1. `threat-scan-orchestrator/SKILL.md` 갱신:
   - **Phase 4.5** `@relationship-graph-analyzer`, **Phase 4.6** `@model-validity-analyzer` 추가(기존 4 skill-security 다음).
   - 최종 리포트 summary에 `graph_verdict` 포함, 각 finding/컴포넌트에 `verdict`/`model_effectiveness` 반영하도록 지시.
   - 제약 사항 문구 정합성 정리(분석=정적, 소스준비만 셸 — 기존 모순 메모 해소).
2. `report-merger/SKILL.md` 갱신: `relationship_findings[]`·`model_validity_findings[]`·`graph_verdict` 병합, ID 일관성 검증(REL-/MODEL-).
3. `bilingual-translator/SKILL.md` 갱신: 신규 필드/용어(verdict·model_effectiveness·graph 용어)를 `dictionary` 기준으로 번역, 비번역 항목(모델 ID 등) 보존.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- 오케스트레이터 파이프라인에 4.5/4.6 단계가 명시되고 호출 규약(`@skill`) 일치.
- 최종 리포트 구조에 `graph_verdict` + 컴포넌트 `verdict`/`model_effectiveness` 포함.
- report-merger가 신규 배열·ID를 병합, bilingual-translator가 EN/KO 병행 산출.
- v2.0.0 기존 7개 분석 카테고리 동작 불변(신규는 추가일 뿐).

## 🔗 선행 의존성

Phase 2, 3.
