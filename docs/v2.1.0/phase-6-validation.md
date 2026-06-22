# Phase 6 — 검증 (Goal Prompt)

> 선행 의존성: **Phase 1–5**

## 🎯 목표 (Objective)

v2.1.0 산출물이 스키마 v1.3을 준수하고, 신규 역량을 산출하며, v2.0.0 기존 동작을 깨지 않음을 샘플 스캔으로 검증한다.

## 📥 참조 입력 (Inputs)

- Phase 1 `docs/claude-threat-scan-json-schema-v1.3.md` / `SCHEMA_V1.3_ENFORCEMENT.md`
- 신규 스킬 2종 + 오케스트레이터(Phase 4)
- 샘플 대상: 연관 컴포넌트(플러그인+스킬+에이전트)와 은퇴 모델 ID·진부화 프롬프트를 포함한 fixture

## 🔧 작업 (Tasks)

1. 샘플 fixture 준비(또는 SkillScan `tests/fixtures` 차용): 악성 에이전트를 번들한 플러그인 + 은퇴 모델 ID 하드코딩 스킬 + 진부화 스캐폴딩 스킬.
2. 오케스트레이터로 샘플 스캔 수행 → v1.3 이중언어 JSON 산출.
3. 검증:
   - **스키마 v1.3 준수**: 금지 필드 0, 신규 필드 전부 optional, ID 접두사(REL-/MODEL-) 정합.
   - **신규 역량 산출**: `graph_verdict` 존재, 위험 전파(번들 악성 에이전트 → 플러그인 verdict 상승), `model_effectiveness` 에 MODEL_LOCKED/OBSOLETE 판정.
   - **이중언어**: `english_report`/`korean_report` 병행, 용어가 dictionary 기준.
   - **v2.0.0 회귀**: 기존 7개 카테고리(static/binary/skill/agent/sensitive/opt/sbom) 정상, 신규 필드 없는 v1.2 페이로드도 유효.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- 샘플 스캔 JSON이 v1.3 스키마 검증 통과.
- `graph_verdict` + 컴포넌트 `verdict` + `model_effectiveness` 포함, 전파 정확(악성 번들 → 상위 REMOVE/DISABLE).
- 은퇴 모델 ID → MODEL_LOCKED, 진부 스캐폴딩 → OBSOLETE 판정 확인.
- EN/KO 병행, 용어 일관.
- v2.0.0 기존 스캔 회귀 정상(신규 필드 미존재 페이로드도 유효).

## 🔗 선행 의존성

Phase 1–5.
