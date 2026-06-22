# Phase 5 — Deep Dive 파이프라인 편입 + code_fix (Goal Prompt)

> 선행 의존성: **없음** (독립). 관련 버그: BUG-003.

## 🎯 목표 (Objective)

메인 오케스트레이터 파이프라인에 **Deep Dive 호출 단계를 명시적으로 편입**하여 Medium↑ finding에 대해 `status`/`deep_dive_result`/`code_fix`를 채우고, 트리아지 수정 코드를 **JSON 무결**하게 격리하여 뷰어에서 **깔끔한 코드블럭**으로 렌더한다.

## 📥 참조 입력 (Inputs)

- `skills/threat-scan-orchestrator/SKILL.md` (스캔 순서 표 L21-37, 분석 전략 L42-52)
- `skills/securityreports-deepdive/SKILL.md` (deep-dive 방법론·출력)
- `docs/claude-threat-scan-json-schema-v1.3.md`, `docs/SCHEMA_V1.3_ENFORCEMENT.md`
- `docs/index.html` (`findingCard`, `detail`, deep_dive_result 렌더 L567)
- `build_claude_desktop.sh` (Sub-Skill 참조표 APPENDEOF)

## 🔧 작업 (Tasks)

1. **오케스트레이터 파이프라인 편입** (`threat-scan-orchestrator/SKILL.md`):
   - 스캔 순서 표에 **단계 8.5 `@securityreports-deepdive`** 추가 (모든 분석기 산출 후, report-merger 이전).
   - 선정 기준: Severity ≥ Medium, status 미정, deep_dive_result 없음, 동작 불명확("could/may/potentially").
   - "분석 전략" Phase 2 서술을 실제 단계(8.5)와 연결.
   - Sub-Skill 참조에 `securityreports-deepdive.md` 명시.
2. **deepdive 스킬 code_fix 추가** (`securityreports-deepdive/SKILL.md`):
   - 출력에 optional `code_fix` 객체 `{language, before?, after, note?}` 추가.
   - **JSON 안전 규칙**: 모든 코드는 JSON 문자열 값으로만, 줄바꿈 `\n`·큰따옴표 `\"`·백슬래시 `\\` 이스케이프. 마크다운 코드펜스 금지. 코드는 `code_fix`에만(prose 금지).
   - v1.2 → v1.3 참조 갱신.
3. **스키마 명문화** (`claude-threat-scan-json-schema-v1.3.md` + `SCHEMA_V1.3_ENFORCEMENT.md`):
   - finding 공통 optional 필드로 `status`/`deep_dive_result`(문자열, 멀티라인 허용)/`code_fix`(객체) 정의.
   - `code_snippet`(자유서술, 금지) vs `code_fix`(구조화, 승인) 구분 명시.
4. **뷰어 렌더** (`docs/index.html`):
   - `code_fix` → 코드블럭 렌더(`<pre><code>`): before(취약, 적색조)/after(수정, 녹색조)/note(서술)/language 라벨.
   - `deep_dive_result` → 줄바꿈 보존(`white-space:pre-wrap`)으로 Level 1/2/3/결론 가독.
   - CSS 코드블럭 스타일(모노스페이스·스크롤·테마색), `t()` 라벨(codeFix/before/after).
5. **병합·번역 pass-through**:
   - `report-merger`: deep-dive 필드(status/deep_dive_result/code_fix) 병합 통과.
   - `bilingual-translator`: `code_fix.before/after`·`language`는 **번역 비대상(코드)**, `deep_dive_result`·`code_fix.note`는 번역.
6. **빌드** (`build_claude_desktop.sh`): Sub-Skill 참조표(APPENDEOF)에 Deep Dive Analyzer 행 추가.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- 오케스트레이터 스캔 순서 표에 `securityreports-deepdive` 단계 존재 (`grep deepdive`).
- deepdive 스킬에 `code_fix` 필드 + JSON 이스케이프 규칙 문구 존재.
- 스키마/enforcement에 `code_fix` 정의 + `code_snippet`과의 구분 명시.
- 뷰어: 코드(따옴표·줄바꿈·`<`/`>` 포함)를 담은 샘플 JSON이 **유효 JSON**이며, `code_fix`가 `<pre><code>` 코드블럭으로 렌더, deep_dive_result 줄바꿈 보존. script 블록 `new Function()` 파싱 통과.
- 빌드 Sub-Skill 참조표에 Deep Dive 행 포함, ZIP 재생성.
- code_fix 없는 기존 페이로드 graceful(무오류).

## 🔗 선행 의존성

없음 (Phase 1–3과 독립). Phase 4 검증은 본 Phase 완료 후 포함.
