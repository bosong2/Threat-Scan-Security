# Changelog

이 프로젝트의 주요 변경 사항을 기록합니다. [Keep a Changelog](https://keepachangelog.com/) 형식과 [Semantic Versioning](https://semver.org/)을 따릅니다.

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
