# Phase 3 — 모델 유효성 스킬 (Goal Prompt)

> 선행 의존성: **Phase 1**

## 🎯 목표 (Objective)

스킬/에이전트가 **특정 모델에 락인**됐는지, **신규 모델이 이미 기능을 대체(진부화)** 했는지를 판정하는 신규 프롬프트 스킬 + 모델 능력 레지스트리를 만든다.

## 📥 참조 입력 (Inputs)

- `dictionary/security-terms-en-ko.json` 형식(신규 JSON 레지스트리 동일 형식)
- Phase 1 v1.3 스키마(`model_validity_findings[]`, `model_effectiveness`)
- MC/OB 패턴·레지스트리 원천: SkillScan `../../SkillScan/docs/ARCHITECTURE.md` §4, `../../SkillScan/engine/skillscan_engine/data/model_capabilities.yaml`

## 🔧 작업 (Tasks)

1. `dictionary/model-capabilities.json` 작성(dictionary JSON 형식):
   - `models`: 모델별 `released`/`context_window`/`native_features`/`native_behaviors`/`deprecated_apis`.
   - `retired_model_ids`: 은퇴 모델 ID 목록.
2. `skills/model-validity-analyzer/SKILL.md` 작성(프롬프트 지시문, 코드 없음):
   - **MC1** 하드코딩/은퇴 모델 ID, **MC2** 컨텍스트 윈도 가정, **MC3** deprecated API 패턴(budget_tokens 등), **MC4** 모델한계 보완 지시문 — 탐지 패턴 표.
   - **OB1** 진부화 힌트(CoT 강제/포맷 강제/청킹 우회/self-critique/역할 부여) — 수집 표.
   - **판정**: 레지스트리와 대조해 `model_effectiveness` ∈ {VALID/DEGRADED/OBSOLETE/MODEL_LOCKED} 부여 + 근거(MC/OB id + 레지스트리 필드 인용).
   - 출력: v1.3 `model_validity_findings[]`(MODEL-NNN) + 컴포넌트 `model_effectiveness`.
3. 한국어 예시: 은퇴 모델 ID 하드코딩 → MODEL_LOCKED; 현재 모델이 기본 수행하는 스캐폴딩 → OBSOLETE.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- `dictionary/model-capabilities.json` 유효 JSON, `models` + `retired_model_ids` 포함.
- `skills/model-validity-analyzer/SKILL.md` 에 MC1-4·OB1 탐지 표 + 판정 매핑 + 근거 인용 지시 + 예시.
- **레지스트리 갱신만으로 판정 변경**(코드 불변) 명시.
- 출력이 Phase 1 v1.3 필드와 일치.

## 🔗 선행 의존성

Phase 1.
