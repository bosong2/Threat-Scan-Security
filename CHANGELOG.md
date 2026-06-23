# Changelog

이 프로젝트의 주요 변경 사항을 기록합니다. [Keep a Changelog](https://keepachangelog.com/) 형식과 [Semantic Versioning](https://semver.org/)을 따릅니다.

## [2.3.5] — 2026-06-23

### Fixed

- **오케스트레이터 컨텍스트 폭발 + 완료 이벤트 오해석 (BUG-06)** — Claude Code에서 Agent 완료 이벤트는 1건씩 개별 도달한다. 오케스트레이터가 대용량 JSON을 8개 수신·Write하면 컨텍스트가 폭발(Churned 3m 50s → 진행 불능), 첫 번째 완료를 "stray notification"으로 오해해 결과를 소실하는 구조적 버그. `agents/tss-*` 분석 워커 13개에 Write 권한 추가 — 각 에이전트가 `OUTPUT_PATH`(프롬프트에서 수신)에 직접 Write하고 짧은 확인 메시지만 반환. 오케스트레이터는 대용량 JSON을 수신·Write할 필요 없이 확인 메시지만 집계하고 체크포인트를 실행한다.

### Changed

- **에이전트 패턴 변경**: `tools: Read` → `tools: Read, Write` (분석 워커 13개). 오케스트레이터 Phase 1–3 지시문을 "OUTPUT_PATH 전달 + 확인 수신" 방식으로 재작성. Desktop `skills/*/SKILL.md`는 무변경 (Dual-Mode 영향 없음).
- `CLAUDE.md` 에이전트 패턴·LLM 실행 경계 섹션 업데이트 (BUG-06 설명 포함).

## [2.3.4] — 2026-06-23

### Fixed

- **오케스트레이터 쉘 변수 유실 (BUG-04)** — Bash 도구는 호출마다 새 쉘을 생성해 `$SCAN_TMP`·`$OUT_DIR`·`$TIMESTAMP` 변수가 유실되는 구조적 문제. `/tmp/tss_session_env` 전역 파일 방식(동시 스캔 충돌 위험)을 제거하고, Phase 0'에서 `=== TSS SESSION VALUES ===` 블록으로 전체 세션값을 한 번에 출력 → LLM이 컨텍스트에 기록하고 이후 모든 Write·Bash 호출에 **실제값을 직접 대입**하는 방식으로 전환. `source` 명령 완전 제거.
- **동시 스캔 경로 충돌** — `mktemp -d` → `mktemp -d -t tss.XXXXXXXX`로 교체해 스캔별 `tss.AbCd1234` 패턴의 인식 가능·고유 임시 디렉터리 생성.
- **TARGET_PATH 미검증 진입** — Phase 0에서 `test -d` Bash 검증 추가. FAIL 시 Phase 1 시작 전 명시적 중단.
- **Monitor 도구 오남용 (BUG-05)** — 오케스트레이터가 Agent 완료 대기에 `Monitor` 도구를 사용해 `InputValidationError` 발생. `Agent()` 호출은 동기(blocking)임을 명시하고 Monitor·폴링 루프 사용 금지 경고 추가.

## [2.3.3] — 2026-06-23

### Security

- **Secret 반환 계약 강제** — `tss-sensitive-patterns`·`tss-static-analyzer` 워커가 raw secret/PII 값을 절대 반환하지 않도록 공유 방법론(`skills/sensitive-pattern-matcher/SKILL.md`, `skills/static-code-analyzer/SKILL.md`)에 **MASKING CONTRACT** 명문화(1차 방어선). `masked_value`(앞 4자+마스킹)만 허용, `value`/`secret`/`raw`/`snippet` 필드 스키마 위반으로 추가.
- **SubagentStop 리댁션 훅** — `hooks/hooks.json` + `scripts/redact_secrets.sh` 신설(2차 방어선). AWS/GitHub/Slack/Private Key/일반 고엔트로피 패턴을 결정론적 정규식으로 마스킹. LLM 호출 없음. Desktop 빌드에서 자동 제외.

### Changed

- **오케스트레이터를 얇은 컨텍스트 master로 재설계** — 워커 산출물을 `$SCAN_TMP/*.json` 파일로 라우팅, 마스터 컨텍스트에 finding 본문 누적 제거. Phase 경계 Bash 무결성 체크포인트(파일 존재·JSON 유효성·secret 가드·`_meta` 집계) 추가. `allowed-tools`에 `Write` 추가(SecurityScanCode `securityscan-triage` 패턴 이식). Opus 사용 권장 노트 추가.
- **모델·권한 차등 정합화** — `tss-deepdive` sonnet → **opus**(최고 난도 트리아지), `tss-binary-analyzer` haiku → sonnet, `tss-model-validity`/`tss-prompt-optimizer` sonnet → haiku(룰 기반·포맷 점검), `tss-translator` haiku → sonnet(번역 품질). 탐지·분석 워커 `tools: Read`(셸·쓰기 구조적 차단), 셸 허용 2개(source-handler·html-report)로 한정.

### Added

- 워커 자기보고 `_meta` footer 규약(`files_scanned`/`findings`/`depthReached`) — 공유 방법론에 명시, 오케스트레이터 Phase 1 체크포인트에서 집계 요약 출력.
- `scripts/agent_efficiency.sh` — 사후 트랜스크립트 기반 per-agent 토큰·turn 효율 요약(best-effort, 미존재 환경 graceful skip).
- `CLAUDE.md` — Claude Code 작업 가이드(Dual-mode 규칙·에이전트 패턴·빌드 동작·스킬 상태).

## [2.3.2] — 2026-06-23

### Fixed

- **오케스트레이터 조기 종료 (BUG-01)** — Claude Code 플러그인에서 8개 에이전트 스폰 후 4.5·4.6·8.5·9·10·11 단계가 실행되지 않고 종료되던 버그. 오케스트레이터 SKILL.md에 SkillScan 패턴의 명시적 Phase 0-5 실행 절차 추가("전부 반환될 때까지 기다린다", "Phase N 완료 후" 명시).
- **Dual-mode 교차 오염 (BUG-02)** — BUG-01 수정 중 추가된 `tss-*` Code 전용 에이전트명이 Desktop SKILL.md에 모드 구분 없이 포함되던 버그. 실행 절차를 `## 실행 절차 — Claude Code Plugin` / `## 실행 절차 — Claude Desktop` 섹션으로 명확히 분리.
- **SBOM description 오염 (BUG-03)** — `securityreports-sbom/SKILL.md` description에 포함된 `tss-sbom`(Code 전용 이름)이 Desktop dist에 복사되던 버그. 모드 중립적 설명으로 교체.

## [2.3.1] — 2026-06-23

### Changed
- **SBOM 명세 파일 전면 확장** — 17개 생태계(npm·PyPI·Maven·Go·Cargo·RubyGems·NuGet·Composer·SwiftPM·Pub·sbt·Hex·Conan/vcpkg·CPAN·Hackage·CocoaPods·CRAN)의 매니페스트 + lock 파일을 인식.
- **Lock 파일 우선 원칙** 도입 — 전이(transitive) 의존성 점검. `requirements.txt`만 보고 `PyJWT`(msal 하위)를 놓치던 문제 해소.
- `repo-indexer`가 lock 파일을 인식하도록 매니페스트 식별 보강.

### Added
- Apache License 2.0 (`LICENSE`, `NOTICE`).
- 문서 세트: `README` · `INSTALLATION` · `USER_GUIDE` · `ARCHITECTURE` · `CHANGELOG` (mermaid 다이어그램, dual-mode).

## [2.3.0] — 2026-06-23

### Added
- **Dual-Mode 지원** — Claude Code 플러그인(`agents/tss-*` 15개 + `commands/threat-scan*` + `.claude-plugin/`)과 Claude Desktop 스킬을 단일 리포지토리에서 동시 지원.
- 단일 원천 구조: Code 에이전트가 `skills/*/SKILL.md` 방법론을 참조(중복 제거).

### Deprecated
- 레거시 `securityreports-{scan,secrets,static,help}` 독립 커맨드 → `/threat-scan` 사용 권장.

## [2.2.0] — 2026-06-22

### Added
- **정적 HTML 리포트 생성**(`@html-report-generator`, 단계 11) — bilingual JSON → 자기완결 HTML. EN/KO 토글·프린트·도넛 차트.
- 결정론적 Python 생성기(`scripts/generate_html_report.py`), 템플릿 단일 원천화(`dictionary/security-template.html`).

## [2.1.x] — 2026

### Added
- 연관관계 그래프 + 위험 전파(단계 4.5), 모델 유효성/진부화 판정(단계 4.6), 조치 verdict 체계.
- 심층 트리아지(단계 8.5) — Medium↑ finding에 status·deep_dive_result·code_fix.

## [2.0.0] — 2026

### Added
- 모듈화된 스킬 파이프라인 기준선(소스 준비·인덱싱·정적·바이너리·민감 패턴·정책·SBOM·병합·번역).
- Schema V1.3 이중 언어 JSON 리포트.

[2.3.1]: #231--2026-06-23
[2.3.0]: #230--2026-06-23
[2.2.0]: #220--2026-06-22
[2.1.x]: #21x--2026
[2.0.0]: #200--2026
