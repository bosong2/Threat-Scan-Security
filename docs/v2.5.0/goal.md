# v2.5.0 — GOAL (goal-mode 마스터 프롬프트)

> **이 문서는 /goal 모드 실행 진입점이다.** 아래 목표·제약·Phase 순서에 따라
> `Phase1.md`~`Phase6.md`의 상세 명세를 차례로 구현한다. 각 Phase의 "완료 조건"이
> 전부 통과해야 다음 Phase로 진행하며, Phase 단위로 커밋한다.

## 목표 (1문장)

v2.5.0은 **① 파이프라인 자율완주 안정화(patch1), ② bilingual enum 표기 일관성(patch2),
③ Compliance Tagging(Schema V1.4 — KISA·AILLM·TA 태그), ④ AI 구성요소 스캔범위 대화식
게이트, ⑤ Claude Code 무정지 진행을 위한 권한 사전등록**을 단일 릴리스로 통합한다.

## 근거 문서 (구현 시 정본 — 충돌 시 이 문서들이 우선)

| 문서 | 내용 |
|------|------|
| [issues/TS-2.5.0-patch1.md](issues/TS-2.5.0-patch1.md) | 플러그인 캐시(2.4.1)에 적용·실측 검증된 패치 — 자율완주·커버리지·번역안정화 + HTML 코드뷰 + AI 구성요소 게이트 |
| [issues/TS-2.5.0_patch2.md](issues/TS-2.5.0_patch2.md) | bilingual enum 비일관 8건 분석·수정 명세 + 권장 조치 섹션 재배치 |
| [issues/TS-2.5.0_PROMPT_compliance_tagging.md](issues/TS-2.5.0_PROMPT_compliance_tagging.md) | Compliance Tagging 구현 프롬프트 (경로는 캐시 기준 — 본 계획의 repo 경로 매핑이 정본) |
| [issues/SCHEMA_V1.4_COMPLIANCE_TAGS.md](issues/SCHEMA_V1.4_COMPLIANCE_TAGS.md) | Schema V1.4 명세 (`compliance_tags` 필드 정의·강제 규칙·렌더러·사전) |
| [issues/compliance-tagmap-distilled.md](issues/compliance-tagmap-distilled.md) | CTID-D — 단계 1–8 태깅 디렉티브 (49 KISA + 9 AILLM + 10 TA) |
| [issues/compliance-tagging-deepdive.md](issues/compliance-tagging-deepdive.md) | CTID-V — 단계 8.5 태그 검증 (V-1~V-7 + 3 sweep) |

## 이슈 → Phase 추적 표 (누락 0 검증)

| 이슈 요구 | 반영 Phase |
|-----------|-----------|
| patch1 PART1-A: 분석 에이전트 Glob/Grep + 완전 열거 | Phase 1 |
| patch1 PART1-B: 번역기 ANTI-HANG·ITEM_RANGE·JSON-SAFETY | Phase 1 |
| patch1 PART1-C: 자율완주·Monitor 대기·nested-root·분할조립 안정화 | Phase 1 |
| patch1 PART2: HTML 코드뷰 다크테마 + 하이라이터 | Phase 5 |
| patch1 PART3: AI 구성요소 스캔범위 게이트 (Phase 0(d)) | Phase 2 |
| patch2 §3.1–3.3: enum 번역 가드레일 + 명세 모순 개정 | Phase 4 (+enforcement은 Phase 3의 v1.4 문서로 흡수) |
| patch2 §3.4: verdict 화이트리스트 (MASK/KEEP 차단) | Phase 4 |
| patch2 §3.5: 템플릿 canonEnum·verd-unknown·SBOM 영어 레이블·섹션 재배치 | Phase 5 |
| compliance Phase 1: Schema V1.4 문서 2종 | Phase 3 |
| compliance Phase 2: CTID 디렉티브 → 스킬 통합 | Phase 3 (문서 배치) + Phase 4 (스킬 편집) |
| compliance Phase 3: validator 스크립트 + 픽스처 | Phase 5 |
| compliance Phase 4: HTML 배지 + 사전 compliance_controls | Phase 5 |
| compliance Phase 5: 오케스트레이터·버전 배선 | Phase 6 |
| compliance Phase 6: E2E 검증 + CHANGELOG | Phase 6 |
| 사용자 요구: 권한 사전등록 (/threat-scan-setup) | Phase 2 |

## 사용자 확정 결정 (재확인 금지 — 그대로 구현)

1. **Monitor 정책 개정**: "Monitor는 서브에이전트 OUTPUT_PATH 파일 생성 대기(`until [ -f ... ]`)
   용도로만 허용, 그 외 폴링 금지"로 개정한다. patch1 실측(Claude Code 런타임이 Agent를
   async로 실행할 수 있음, 2026-07-15 재현 완주)이 근거. CLAUDE.md·오케스트레이터의
   기존 "Monitor 금지(BUG-05)" 문구를 동시 갱신한다(BUG-05 이력은 "파라미터 오용 금지"로 재해석).
2. **권한 자동 셋업 (오케스트레이터 내장)**: `/threat-scan` 시작 시 오케스트레이터가 권한 규칙
   부재를 감지하면 **자동으로** `.claude/settings.local.json`에 allow 규칙을 병합 등록한다 —
   이때 Write 권한 프롬프트가 사용자 확인·승인 **1회**로 작동하고, 이후 무정지 완주.
   `/threat-scan-setup` 커맨드는 사전 등록용 수동 경로로 존치(규칙 목록은 오케스트레이터가 정본).
3. **AI 구성요소 게이트는 양 모드 공통**: Code는 `AskUserQuestion` 1회, Desktop은 대화 질의로
   동일 방법론 수행. 자율완주의 허용 상호작용은 정확히 2가지 — ①셋업 Write 승인(부재 시 1회),
   ②게이트 질문(발견 시 1회).

## 불변 제약

1. **Dual-Mode 동시 수정** — 공유 자산(skills/·dictionary/·scripts/*.py·docs/ 스키마)은 1회
   수정으로 양 모드 반영되지만, Code 전용(agents/·commands/·hooks/)과 Desktop 빌드 회귀
   검증은 별도로 수행한다. 오케스트레이터 SKILL.md의 Code/Desktop 섹션 경계(BUG-02) 준수.
2. **Schema v1.3 문서 보존** — `docs/claude-threat-scan-json-schema-v1.3.md`·
   `docs/SCHEMA_V1.3_ENFORCEMENT.md`는 **무수정 보존**(legacy 참조). V1.4 문서를 신설하고
   v1.4가 정본이 된다(기존 v1.2→v1.3 관례). patch2가 지시한 v1.3 enforcement 개정은
   **v1.4 enforcement에 흡수**한다.
3. **LLM·셸 실행 경계** — 단계 1–10 추론 전용 유지. 셸 허용 예외: 단계 0·10.5(조립)·11.
   `validate_compliance_tags.py`는 단계 11 계열(HTML 생성 직전)에서 실행.
4. **템플릿-뷰어 심링크 불변** — `docs/index.html`은 `dictionary/security-template.html`의
   심링크. 템플릿만 수정하면 자동 동기(별도 편집 금지).
5. **태그 불변 토큰** — `compliance_tags`는 EN/KO byte-identical. 로컬라이즈 금지.
6. **태깅 금지 위치** — `prompt_optimization[]`·`recommendations[]`·`scan_metadata`·
   `repository_summary`·`graph_verdict`에는 태그를 달지 않는다.
7. **캐시 검증본 이식** — patch1 코드는
   `~/.claude/plugins/cache/threat-scan-security-marketplace/threat-scan-security/2.4.1/`에
   검증된 구현본이 존재한다. 해당 구현을 repo 구조에 맞게 이식하고 재발명하지 않는다.

## Phase 구성·의존

| Phase | 문서 | 내용 | 의존 |
|-------|------|------|------|
| 1 | [Phase1.md](Phase1.md) | 파이프라인 자율완주·커버리지·번역 안정화 (patch1 PART1) | — |
| 2 | [Phase2.md](Phase2.md) | AI 구성요소 스캔범위 게이트 + `/threat-scan-setup` 권한 사전등록 | — (1과 병행 가능하나 오케스트레이터 동시 수정 충돌 방지 위해 1 이후 권장) |
| 3 | [Phase3.md](Phase3.md) | Schema V1.4 문서 세트 + CTID 디렉티브 정식 배치 | — |
| 4 | [Phase4.md](Phase4.md) | 스킬·에이전트 계층 일괄 개정 (CTID-D/V 통합 + patch2 가드레일) | 3 |
| 5 | [Phase5.md](Phase5.md) | validator + 사전 compliance_controls + HTML 템플릿 통합 개편 | 3, 4 |
| 6 | [Phase6.md](Phase6.md) | 버전 배선(2.5.0/V1.4) + E2E 검증 + Desktop 빌드 회귀 | 1–5 전부 |

**실행 순서: 1 → 2 → 3 → 4 → 5 → 6 (순차 권장).** 오케스트레이터 SKILL.md는 Phase 1·2·6이
연속으로 수정하므로 반드시 순차로. 템플릿은 Phase 5 한 곳에서만 수정한다.

## 완료 정의 (Definition of Done)

- [ ] **P1** 9개 분석 에이전트 `tools: Read, Write, Glob, Grep`, 번역기 ANTI-HANG 계약,
      오케스트레이터 자율완주+Monitor 대기, CLAUDE.md 정책 개정. Desktop 섹션 미오염.
- [ ] **P2** AI 구성요소 발견 시 정확히 1회 질문 후 완주(미발견 시 무질문),
      `ai_agent_scope` 기록, `/threat-scan-setup`이 settings.local.json에 규칙 병합.
- [ ] **P3** v1.4 스키마·enforcement 문서 신설(v1.3 무수정), CTID 2건 docs/ 정식 배치,
      태그 regex가 두 문서에 정확히 1회씩.
- [ ] **P4** 8개 emitting 스킬에 태깅 블록 각 1개, deepdive에 CTID-V 폴딩, translator
      enum 번역 금지 + "등급 번역" 문구 0건, sensitive verdict 화이트리스트.
- [ ] **P5** validator 픽스처 3종 통과/검출, 사전 59태그, 템플릿에서 patch2 8개 증상
      전부 해소 + 태그 배지 + 다크 코드뷰 + 권장 조치가 리포지토리 요약 직후.
- [ ] **P6** 버전 2.5.0 정합(VERSION·plugin.json·help·scanner_version "V2.5"·CHANGELOG),
      픽스처 repo E2E 통과(validator exit 0·태그 기대 일치·EN=KO byte-identical),
      Desktop 빌드 회귀 전부 통과.
- [ ] 커밋·태그 v2.5.0 완료 (push는 사용자 승인 후).

## 범위 밖 (구현 금지)

- 신규 파이프라인 단계 추가(태깅은 기존 단계에 폴딩), 신규 finding 배열,
  `findings_summary`/`executive_summary`(여전히 금지).
- `prompt_optimization`·`recommendations` 태깅, 태그 문자열 로컬라이즈, KISA 제어번호 변경.
- 스크립트의 라이브 웹 호출(OSV 질의는 브라우저 런타임 한정 — 기존 원칙 유지).
- korean_report에서 enum 필드 생략하는 구조 개편(중복 제거) — 차기 버전 검토.
