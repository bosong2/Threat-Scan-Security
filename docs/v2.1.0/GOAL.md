# Threat-scan-security v2.1.0 — 마스터 Goal Prompt

> Claude Code의 **Dynamic Workflow `goal` 기능**에 그대로 투입하기 위한 v2.1.0 최상위 목표.
> 자율 루프는 Phase 순서대로 하나씩 추구하고, 각 Phase의 **완료 조건(Acceptance)** 을 만족하면 다음으로 진행한다.
> 기준선: v2.0.0(= 기존 SecurityScan 복제, `../../VERSION`).

---

## 🎯 목표 (한 문장)

> **Claude Desktop 호환 프롬프트 스킬만으로, Threat-scan-security에 ① 컴포넌트 연관관계 그래프 + 위험 전파, ② 모델 유효성/진부화 판정, ③ 조치 verdict 체계를 추가한다.**

새 코드 엔진·훅 없이, 기존 SecurityScan의 구조(SKILL.md + dictionary JSON + schema + `build_claude_desktop.sh`)를 그대로 따른다. SkillScan에서 검증한 방법론을 **프롬프트 스킬로 이식**한다.

신규 verdict 체계:
- 보안/그래프: `INSTALL_OK / REVIEW / DISABLE / REMOVE`
- 모델 효과성: `VALID / DEGRADED / OBSOLETE / MODEL_LOCKED`

---

## 🔒 불변 제약 (절대 변경 금지)

1. **Claude Desktop 우선 / 네트워크 불요** — 모든 신규 분석은 Claude 프롬프트 추론. 코드 실행·외부 API 호출 없음. (Desktop 샌드박스 기본 네트워크 off에서 동작)
2. **기존 쉘/모듈 구조 유지** — 산출물은 `skills/*/SKILL.md` + `dictionary/*.json` + `docs/*schema*.md` + `build_claude_desktop.sh` 갱신만. **새 .py 엔진·PreToolUse 훅 도입 금지.**
3. **하위호환 스키마** — v1.2를 깨지 않고 v1.3로 확장. **신규 필드는 전부 optional**, 금지 필드 추가 안 함(뷰어 호환 유지).
4. **이중언어(EN/KO) 유지** — 신규 용어는 `dictionary/`에 등록, `bilingual-translator`가 처리.
5. **정적 분석 원칙** — 검사 대상 코드 미실행. 소스 준비(git clone/unzip)만 `source-handler`가 셸 사용.

**범위 밖 (이번에 하지 않음)**: YARA, 라이브 OSV CVE, PreToolUse 설치-게이트, 결정론 Python 탐지기(Option B). 모두 Desktop 비호환이거나 별도 버전(v2.1.x) 대상.

---

## ✅ 완료 정의 (Definition of Done)

1. 샘플 대상 스캔이 **연관관계 그래프 + 위험 전파**, **모델 유효성/진부화**, **컴포넌트·그래프 verdict** 를 포함한 v1.3 이중언어 JSON을 산출.
2. 신규 스킬 2종(`relationship-graph-analyzer`, `model-validity-analyzer`)이 오케스트레이터 파이프라인에 편입됨.
3. v1.3 스키마 검증 통과(금지 필드 0, 신규 필드 optional), EN/KO 병행 출력.
4. **v2.0.0 기존 스캔 회귀 정상**(신규 필드는 추가일 뿐 기존 동작 불변).
5. `build_claude_desktop.sh` 가 신규 스킬·`model-capabilities.json`·v1.3 docs 포함하여 `threat-scan-security.zip` 재생성, VERSION=2.1.0.

---

## 🗺️ Phase 진행 순서

| # | Phase | 문서 | 선행 의존성 |
|---|---|---|---|
| 1 | Verdict 체계 & Schema v1.3 | [phase-1-verdict-schema-v1.3.md](./phase-1-verdict-schema-v1.3.md) | 없음 |
| 2 | 연관관계 그래프 스킬 | [phase-2-relationship-graph-skill.md](./phase-2-relationship-graph-skill.md) | 1 |
| 3 | 모델 유효성 스킬 | [phase-3-model-validity-skill.md](./phase-3-model-validity-skill.md) | 1 |
| 4 | 오케스트레이터 통합 | [phase-4-orchestrator-integration.md](./phase-4-orchestrator-integration.md) | 2, 3 |
| 5 | 빌드 & 패키징 | [phase-5-build-packaging.md](./phase-5-build-packaging.md) | 1–4 |
| 6 | 검증 | [phase-6-validation.md](./phase-6-validation.md) | 1–5 |

---

## 🔁 자율 루프 운영 지침

1. **현재 Phase 식별**: `Threat-scan-security/` 상태 점검, 완료 Phase의 Acceptance 재확인.
2. **단일 Phase 집중**: 의존성 충족된 가장 앞선 미완료 Phase 하나만.
3. **Acceptance 검증**: JSON 스키마 v1.3 유효성, dictionary EN-KO 키 존재, 샘플 스캔 산출물의 신규 필드 확인, v2.0.0 회귀.
4. **불변 제약 self-check**: 매 Phase 전 5개 제약 — 특히 (1) 프롬프트 전용·네트워크 불요, (2) 새 .py/훅 금지, (3) optional 필드.
5. **종료 판단**: 전 Phase Acceptance + DoD 충족 시 종료.

---

## 📌 참조 (기존 v2.0.0 자산)

- 오케스트레이터: `skills/threat-scan-orchestrator/SKILL.md`
- 기존 스킬 보안 분석(3단계 추적): `skills/skill-security-analyzer/SKILL.md`
- 스키마: `docs/claude-threat-scan-json-schema-v1.2.md`, `docs/SCHEMA_V1.2_ENFORCEMENT.md`
- 사전: `dictionary/security-terms-en-ko.json`, `dictionary/translation-rules-ko.json`
- 빌드: `build_claude_desktop.sh`
- 방법론 원천(참고): SkillScan `../../SkillScan/docs/ARCHITECTURE.md` (그래프 스키마·전파 규칙·MC/OB·verdict 매핑)
