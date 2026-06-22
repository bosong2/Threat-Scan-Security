# Phase 1 — Verdict 체계 & Schema v1.3 (Goal Prompt)

> 선행 의존성: **없음** (기반 Phase)

## 🎯 목표 (Objective)

조치 verdict 체계를 정의하고, 기존 출력 스키마를 **하위호환 v1.3**으로 확장한다. 이후 모든 신규 스킬이 v1.3 필드를 산출한다.

## 📥 참조 입력 (Inputs)

- `docs/claude-threat-scan-json-schema-v1.2.md` (v1.2 기준 — 복제 후 확장)
- `docs/SCHEMA_V1.2_ENFORCEMENT.md` (금지/필수 필드 규칙)
- `dictionary/security-terms-en-ko.json` (용어 등록 대상)
- 매핑 규칙 원천(참고): SkillScan `../../SkillScan/docs/ARCHITECTURE.md` §5 Verdict

## 🔧 작업 (Tasks)

1. `docs/claude-threat-scan-json-schema-v1.3.md` 신설(v1.2 전문 복제 후 확장):
   - 각 finding에 **optional** `verdict` ∈ {`INSTALL_OK`,`REVIEW`,`DISABLE`,`REMOVE`}.
   - 컴포넌트/그래프 레벨 **optional** `model_effectiveness` ∈ {`VALID`,`DEGRADED`,`OBSOLETE`,`MODEL_LOCKED`}.
   - 리포트 summary에 **optional** `graph_verdict` 객체(`security_verdict`, `worst_component`, `rationale`).
   - 신규 finding 배열 2종(optional): `relationship_findings[]`(REL-NNN), `model_validity_findings[]`(MODEL-NNN).
2. **verdict 산정 규칙** 문서화:
   - severity→verdict 매핑: Critical→REMOVE, High→DISABLE, Medium→REVIEW, Low/Info→INSTALL_OK.
   - 모델 강등: `OBSOLETE`/`MODEL_LOCKED` 는 INSTALL_OK를 REVIEW로 강등.
   - 그래프 verdict = 전파 후 최악 컴포넌트의 verdict.
3. `docs/SCHEMA_V1.3_ENFORCEMENT.md` 작성: 신규 필드 전부 optional, v1.2 금지필드 정책 유지, ID 접두사(REL-/MODEL-) 등록.
4. `dictionary/security-terms-en-ko.json` 에 신규 용어 추가: verdict 4종, model_effectiveness 4종, "relationship/graph/risk propagation/model validity/obsolescence" 등 EN-KO 매핑.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- `docs/claude-threat-scan-json-schema-v1.3.md` 존재, 신규 필드 **모두 optional**로 명시(v1.2 페이로드가 v1.3에서도 유효).
- severity→verdict 매핑 + 그래프 전파 규칙 명문화.
- `SCHEMA_V1.3_ENFORCEMENT.md` 에 금지필드 0 추가 확인.
- dictionary에 verdict/model_effectiveness EN-KO 키 존재(`grep` 확인 가능).

## 🔗 선행 의존성

없음.
