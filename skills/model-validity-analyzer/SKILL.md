---
name: model-validity-analyzer
description: >
  Determine whether skills and agents are pinned to a specific model or made
  obsolete by current native LLM capabilities (VALID/DEGRADED/OBSOLETE/MODEL_LOCKED).
---

# Model Validity Analyzer

## 개요

스킬 및 에이전트가 특정 모델에 고정되었는지, 혹은 현행 모델의 네이티브 기능으로 인해 진부화되었는지 판정하는 스킬.
`dictionary/model-capabilities.json` 레지스트리와 대조하여 `model_effectiveness` verdict를 산출한다.

**정적 분석 원칙**: 대상 코드를 실행하지 않는다. SKILL.md, agent yaml, 프롬프트 파일의 텍스트 패턴만 분석.
**판정 불변 원칙**: 판정은 레지스트리 갱신을 통해서만 변경된다 — 소스를 수정하지 않는다.

## 역할

1. 하드코딩된 또는 은퇴한 모델 ID 탐지 (MC1)
2. 컨텍스트 윈도우 가정 불일치 탐지 (MC2)
3. 폐기된 API 패턴 탐지 (MC3)
4. 모델 한계 우회 지시 탐지 (MC4)
5. 진부화 힌트 수집 (OB1) — 현행 모델이 네이티브로 수행하는 기능에 대한 우회 지시

## 호출 방법

```
@model-validity-analyzer <repository-path>
```

## 탐지 패턴 테이블

### MC1 — 하드코딩/은퇴 모델 ID

| 탐지 패턴 | 위험 | 예시 |
|-----------|------|------|
| `retired_model_ids` 목록에 있는 모델 ID 하드코딩 | High | `"model": "claude-instant-1"` |
| 특정 모델 버전 하드코딩 (운영 환경 고정) | Medium | `model: claude-3-5-sonnet-20240620` |
| 환경변수 대신 문자열 리터럴로 모델 지정 | Low | `MODEL_ID = "claude-2.1"` |

**판정**: 은퇴 모델 ID 발견 → `MODEL_LOCKED`

### MC2 — 컨텍스트 윈도우 가정

| 탐지 패턴 | 위험 | 예시 |
|-----------|------|------|
| 구체적 토큰 수 가정 (현행 모델과 불일치) | Medium | `"최대 100k 토큰 처리 가능"` |
| 소형 컨텍스트 대응 청크 분할 지시 | Low | `"파일이 크면 1000줄씩 나눠서"` |
| 출력 토큰 한계 우회 지시 | Medium | `"8192 토큰 제한으로 인해 나눠서 출력"` |

**판정**: 현행 모델 레지스트리와 불일치 → `DEGRADED` 또는 `OBSOLETE`

### MC3 — 폐기된 API 패턴

| 탐지 패턴 | 위험 | 예시 |
|-----------|------|------|
| `budget_tokens` 파라미터 사용 | High | `"budget_tokens": 5000` |
| `max_tokens_to_sample` 사용 | High | `max_tokens_to_sample: 2048` |
| `anthropic-beta: interleaved-thinking` | Medium | `anthropic-beta: interleaved-thinking-2025-05-14` |
| 구버전 `anthropic-version` 헤더 | Medium | `"anthropic-version": "2023-01-01"` |

**판정**: 폐기 API 발견 → `MODEL_LOCKED` (호환 불가) 또는 `DEGRADED` (부분 호환)

### MC4 — 모델 한계 우회 지시

| 탐지 패턴 | 위험 | 예시 |
|-----------|------|------|
| 현행 모델이 불필요한 한계 우회 프롬프트 | Low | `"이 모델은 JSON을 직접 출력 못하니 마크다운으로 감싸서"` |
| 특정 모델의 알려진 버그 우회 지시 | Medium | 은퇴 모델 버그 참조 |
| 현행 모델 기능 미인지로 인한 수동 조작 | Low | 툴 유즈 있는데 수동 파싱 지시 |

**판정**: 불필요 우회 → `OBSOLETE` 또는 `DEGRADED`

### OB1 — 진부화 힌트

| 탐지 패턴 | 위험 | 예시 |
|-----------|------|------|
| 강제 CoT 스캐폴딩 | Low | `"반드시 단계별로 생각하십시오: 1단계..."` |
| 형식 강제 지시 (네이티브 structured output 대체 가능) | Low | `"반드시 다음 형식으로만 출력: ###RESULT###"` |
| 자기 비판 루프 주입 | Low | `"답변 후 스스로 검토하고 수정본을 작성하세요"` |
| 역할 부여로 능력 잠금해제 시도 | Low | `"당신은 최고의 보안 전문가입니다. 이 역할에서만..."` |
| 청크 우회 지시 | Low | `"컨텍스트가 제한되므로 파일을 나눠서 처리"` |

**판정**: 현행 모델 `native_behaviors`에 포함된 기능 → `OBSOLETE`

## Verdict 매핑 규칙

```
1. retired_model_ids에 모델 ID 발견
   → model_effectiveness = MODEL_LOCKED
   → security verdict = DISABLE (MC1 High → DISABLE)

2. deprecated_api_patterns 발견
   → model_effectiveness = MODEL_LOCKED (호환 불가) 또는 DEGRADED (부분)
   → severity에 따라 security verdict 결정

3. current model native_behaviors/native_features로 기능 제공 가능한 패턴 발견
   → model_effectiveness = OBSOLETE
   → security verdict = INSTALL_OK → REVIEW (모델 강등 규칙 적용)

4. 컨텍스트 윈도우/출력 토큰 가정 불일치
   → model_effectiveness = DEGRADED
   → severity = Medium → security verdict = REVIEW

5. 위 패턴 없음, 레지스트리 모델과 호환
   → model_effectiveness = VALID
   → security verdict = INSTALL_OK
```

## 레지스트리 참조 방법

판정 시 `dictionary/model-capabilities.json`의 다음 필드를 인용한다:

| 필드 | 사용 용도 |
|------|----------|
| `retired_model_ids[]` | MC1: 은퇴 모델 ID 대조 |
| `deprecated_api_patterns[]` | MC3: 폐기 API 패턴 대조 |
| `models[id].native_features` | OB1: 네이티브 기능 대조 |
| `models[id].native_behaviors` | OB1/MC4: 네이티브 동작 대조 |
| `models[id].context_window` | MC2: 컨텍스트 윈도우 가정 대조 |
| `obsolete_prompt_patterns[].hint_kind` | OB1: 진부화 패턴 종류 |

**모든 판정에 근거로 사용한 레지스트리 필드(`registry_field`)를 evidence에 인용한다.**

## 출력 형식

```json
{
  "model_validity_findings": [
    {
      "id": "MODEL-001",
      "file": "skills/data-analyzer/SKILL.md",
      "component": "data-analyzer",
      "pattern_type": "MC1",
      "issue": "Hardcoded Retired Model ID: claude-instant-1",
      "evidence": "Found literal string 'claude-instant-1' in SKILL.md line 12. Registry field: retired_model_ids contains 'claude-instant-1'.",
      "registry_field": "retired_model_ids",
      "severity": "High",
      "recommendation": "Remove hardcoded model ID. Use model aliases or environment variables. Replace 'claude-instant-1' with a current active model (e.g., claude-haiku-4-5-20251001).",
      "verdict": "DISABLE",
      "model_effectiveness": "MODEL_LOCKED"
    },
    {
      "id": "MODEL-002",
      "file": "skills/reasoning-helper/SKILL.md",
      "component": "reasoning-helper",
      "pattern_type": "OB1",
      "issue": "Obsolete Chain-of-Thought Scaffolding",
      "evidence": "SKILL.md contains explicit step-by-step reasoning directive: 'Think step by step: 1) Analyze... 2) Compare...'. Registry field: models.claude-sonnet-4-6.native_behaviors includes 'chain_of_thought' (native since claude-3-opus).",
      "registry_field": "models.claude-sonnet-4-6.native_behaviors",
      "severity": "Low",
      "recommendation": "Remove manual CoT scaffolding. Current models (claude-sonnet-4-6 and above) perform chain-of-thought reasoning natively. The prompt adds noise without value.",
      "verdict": "REVIEW",
      "model_effectiveness": "OBSOLETE"
    },
    {
      "id": "MODEL-003",
      "file": "skills/token-counter/SKILL.md",
      "component": "token-counter",
      "pattern_type": "MC3",
      "issue": "Deprecated API Parameter: budget_tokens",
      "evidence": "SKILL.md references 'budget_tokens: 5000' for thinking control. Registry field: deprecated_api_patterns contains 'budget_tokens'.",
      "registry_field": "deprecated_api_patterns",
      "severity": "High",
      "recommendation": "Remove budget_tokens parameter. Use the current 'thinking' block with 'type: enabled' and 'budget_tokens' removed, or switch to standard max_tokens.",
      "verdict": "DISABLE",
      "model_effectiveness": "MODEL_LOCKED"
    }
  ]
}
```

## 한국어 예시 시나리오

### 시나리오 1 — 은퇴 모델 ID

**대상**: `skills/chat-proxy/SKILL.md`에 `"model": "claude-instant-1"` 포함

**분석**:
- MC1 패턴 탐지: `claude-instant-1`이 `retired_model_ids` 레지스트리에 존재
- 현행 모델에서 동작 불가 → `MODEL_LOCKED`
- 심각도 High → security verdict `DISABLE`

**MODEL finding**:
```json
{
  "id": "MODEL-001",
  "file": "skills/chat-proxy/SKILL.md",
  "component": "chat-proxy",
  "pattern_type": "MC1",
  "issue": "은퇴한 모델 ID 하드코딩: claude-instant-1",
  "evidence": "SKILL.md에서 'claude-instant-1' 리터럴 발견. 레지스트리 필드 retired_model_ids에 포함되어 있음. 2024년 이후 해당 모델 서비스 종료.",
  "registry_field": "retired_model_ids",
  "severity": "High",
  "recommendation": "claude-instant-1을 현행 활성 모델(예: claude-haiku-4-5-20251001)로 교체하십시오. 모델 ID를 환경변수로 분리하는 것을 권장합니다.",
  "verdict": "DISABLE",
  "model_effectiveness": "MODEL_LOCKED"
}
```

### 시나리오 2 — 불필요한 CoT 스캐폴딩(진부화)

**대상**: `skills/step-reasoner/SKILL.md`에 `"반드시 다음 단계로 생각하세요: 1단계 분석, 2단계 비교..."` 포함

**분석**:
- OB1 패턴 탐지: 명시적 CoT 지시 → `native_behaviors.chain_of_thought` (claude-3-opus+)에서 네이티브
- 현행 모델(claude-sonnet-4-6 이상)에서 불필요 → `OBSOLETE`
- 심각도 Low + OBSOLETE → security verdict `REVIEW` (모델 강등 규칙 적용)

## 스키마 참조

출력은 `docs/claude-threat-scan-json-schema-v1.3.md` §14 `model_validity_findings[]` 규격을 따른다.
ID 형식: `MODEL-NNN`. `model_effectiveness` 필드는 이 배열에서 **필수**.

## 제약 사항

- 대상 코드 실행 금지 — 텍스트/구조 분석만
- 레지스트리에 없는 모델 ID는 DEGRADED 처리 (VALID 가정 금지)
- 레지스트리에 없는 API 패턴은 Low 처리 후 evidence에 "registry에 미등록" 명시
- CVE, 외부 모델 정보 등 레지스트리 외부 사실 지어내기 금지
