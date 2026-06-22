# Threat-scan-security v2.1.1 — 마스터 Goal Prompt

> Claude Code의 **Dynamic Workflow `goal` 기능**에 그대로 투입하기 위한 v2.1.1 패치 목표.
> 자율 루프는 Phase 순서대로 하나씩 추구하고, 각 Phase의 **완료 조건(Acceptance)** 을 만족하면 다음으로 진행한다.
> 기준선: v2.1.0(`../../VERSION`). 본 버전은 **버그 패치**다 — 상세는 [BUGREPORT.md](./BUGREPORT.md).

---

## 🎯 목표 (한 문장)

> **권장 조치(recommendations)에 추적 가능한 ID(REC-NNN)·근거 finding 역참조(finding_ids)·rank/priority 분리를 도입하여, "어떤 기준으로 뽑힌 권장인지" 판단 가능하게 만든다.**

v2.1.0 검증 후 정합성 점검에서 발견된 2건의 결함(권장조치 추적성 부재, priority 타입 불일치)을 스키마·스킬·번역·뷰어 전 계층에 일관 반영하여 수정한다. 신규 코드 엔진·훅 없이 기존 구조(SKILL.md + dictionary JSON + schema + `build_claude_desktop.sh`)를 따른다.

---

## 🔒 불변 제약 (절대 변경 금지)

1. **Claude Desktop 우선 / 네트워크 불요** — 신규 분석은 Claude 프롬프트 추론. 코드 실행·외부 API 호출 없음.
2. **기존 쉘/모듈 구조 유지** — 산출물은 `skills/*/SKILL.md` + `dictionary/*.json` + `docs/*schema*.md` + `docs/index.html` + `build_claude_desktop.sh` 갱신만. 새 .py 엔진·훅 도입 금지.
3. **하위호환 스키마** — v1.2/v1.3을 깨지 않고 보강. **신규 필드(id/rank/finding_ids)는 전부 optional**, 금지 필드 추가 안 함(뷰어 호환 유지).
4. **이중언어(EN/KO) 유지** — 신규 라벨은 `dictionary/`·뷰어 `t()`에 등록. `id`/`rank`/`finding_ids`/`priority`는 번역 비대상.
5. **정적 분석 원칙** — 검사 대상 코드 미실행.

**범위 밖 (이번에 하지 않음)**: recommendations에 verdict 직접 부여(finding_ids 경유로 충분), 라이브 OSV 연계 변경, 신규 스킬 추가, 스키마 메이저 버전 승급(v1.4 신설 안 함 — v1.3 보강).

---

## ✅ 완료 정의 (Definition of Done)

1. recommendations 각 항목이 `id`(REC-NNN) + `rank`(정수) + `priority`(문자열) + `finding_ids`(기존 finding 참조) 를 포함하는 계약으로 스키마 §15에 명문화됨.
2. report-merger가 위 계약대로 권장조치를 생성(priority=참조 finding 최고 severity, rank=정렬 순번, finding_ids=근거)하도록 지시문 갱신됨.
3. 뷰어가 권장조치 카드에 REC-id·rank·priority 뱃지와 finding_ids 칩을 렌더하고, 칩 클릭 시 해당 finding 카드로 스크롤·섹션 자동 펼침.
4. **v2.1.0 하위호환 회귀 정상** — id/rank/finding_ids/code_fix 없는 기존 페이로드도 뷰어 오류 없이 렌더.
5. `VERSION=2.1.1`, `build_claude_desktop.sh` 빌드 성공, `threat-scan-security.zip` 재생성.
6. **Deep Dive 실행**: 오케스트레이터 파이프라인이 Medium↑ finding에 대해 deep-dive를 호출하여 `status`/`deep_dive_result`/`code_fix`를 채우고, 빌드 Sub-Skill 참조표에 deepdive 포함. 수정 코드는 `code_fix`로 격리되어 JSON 무결, 뷰어에서 코드블럭으로 렌더.

---

## 🗺️ Phase 진행 순서

| # | Phase | 문서 | 선행 의존성 |
|---|---|---|---|
| 1 | recommendations 스키마 계약 | [phase-1-recommendations-schema.md](./phase-1-recommendations-schema.md) | 없음 |
| 2 | report-merger 생성 + 번역 + 사전 | [phase-2-report-merger-generation.md](./phase-2-report-merger-generation.md) | 1 |
| 3 | 뷰어 추적성 UI | [phase-3-viewer-traceability.md](./phase-3-viewer-traceability.md) | 1 |
| 5 | Deep Dive 파이프라인 편입 + code_fix | [phase-5-deepdive-integration.md](./phase-5-deepdive-integration.md) | 없음 |
| 4 | 버전·빌드·검증 | [phase-4-validation.md](./phase-4-validation.md) | 1–3, 5 |

---

## 🔁 자율 루프 운영 지침

1. **현재 Phase 식별**: 완료 Phase의 Acceptance 재확인.
2. **단일 Phase 집중**: 의존성 충족된 가장 앞선 미완료 Phase 하나만.
3. **Acceptance 검증**: `grep REC-NNN` 일관성, 뷰어 칩 클릭 동작, v2.1.0 회귀.
4. **불변 제약 self-check**: 매 Phase 전 5개 제약 — 특히 (3) optional 필드, (4) 번역 비대상.
5. **종료 판단**: 전 Phase Acceptance + DoD 충족 시 종료.

---

## 📌 참조 (기존 v2.1.0 자산)

- 스키마: `docs/claude-threat-scan-json-schema-v1.3.md`(§15 recommendations, §17 ID표), `docs/SCHEMA_V1.3_ENFORCEMENT.md`
- 병합/번역: `skills/report-merger/SKILL.md`, `skills/bilingual-translator/SKILL.md`
- 사전: `dictionary/security-terms-en-ko.json`, `dictionary/translation-rules-ko.json`
- 뷰어: `docs/index.html`(`renderRecs`, `findingCard`, `toggleSection`)
- 빌드: `build_claude_desktop.sh`, `VERSION`
- 결함 근거: `scanreport-20260622143000.json`(recommendations priority 정수·finding_ids 부재)
