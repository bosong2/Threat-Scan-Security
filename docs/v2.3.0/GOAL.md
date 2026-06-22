# v2.3.0 — Claude Code Dual-Mode 통합

## 목표 (1문장)

Claude Desktop 전용이던 Threat-scan-security를, **동일 리포지토리에서 Claude Code 플러그인으로도 동작**하도록 에이전트(`agents/tss-*.md`)·커맨드(`commands/threat-scan*.md`) 계층을 추가하고, 기존 Desktop 자산(`skills/*/SKILL.md`·`dictionary/`·`scripts/`)을 두 모드가 공유하게 한다.

## 배경

현재 패키지는 `build_claude_desktop.sh`가 파이프라인 전체를 단일 Desktop 스킬(`threat-scan-orchestrator` SKILL.md + `references/sub-skills/*.md`)로 묶어 Claude Desktop에만 배포된다. Claude Code에는 진입점(커맨드)·서브에이전트 정의가 없어 동작하지 않는다.

탐색 결과 `skills/*/SKILL.md` 18개가 **이미 Claude Code 디렉토리 레이아웃**(`skills/<name>/SKILL.md`)을 따르고 있어, frontmatter 추가 + 에이전트/커맨드 계층만 얹으면 Desktop 본문을 그대로 재사용하며 dual-mode가 가능하다. SkillScan 플러그인의 검증된 패턴(메인 스킬이 `allowed-tools: Agent(...)`로 워커 에이전트를 오케스트레이션)을 채택한다.

사용자는 작업을 **① v2.3.0 = Claude Code 통합 → ② 이후 별도 버전 = 플러그인 배포 패키징**으로 분리했다. 이번 버전은 통합·로컬 동작까지가 범위다.

## 사용자 확정 결정

- **아키텍처**: Agents-based (SkillScan식). `agents/tss-*.md` 워커 15개 + `commands/threat-scan*.md` + 오케스트레이션은 스킬 레벨 유지(서브에이전트 중첩 불가).
- **레거시 `securityreports-*`(5개)**: 삭제하지 않고 **deprecated 표기** + 신규 `/threat-scan` 안내.

## 불변 제약 (계승 + 신규)

1. **Desktop 하위호환**: `build_claude_desktop.sh`와 `skills/*/SKILL.md` **본문**은 불변. Desktop 빌드 산출물(zip 구성·동작) 동일성 유지. 추가하는 frontmatter는 Desktop 빌드에서 무해해야 한다.
2. **단일 원천(Single Source of Truth)**: 분석 방법론은 `skills/<name>/SKILL.md`에만 둔다. `agents/tss-*.md`는 본문을 복제하지 않고 해당 SKILL.md를 **참조**한다. (Desktop·Code 양 모드 공유)
3. **결정론·LLM 경계 계승**: 단계 1–10은 코드 실행·파일 생성 금지(Claude 추론). 단계 0(소스 준비)·단계 11(HTML 생성)만 스크립트/파일 생성 허용 — 이 경계를 Code 모드에서도 동일 적용.
4. **공유 자산**: `dictionary/`(템플릿·사전)·`scripts/`(생성기)는 두 모드가 공유. 경로 해석만 모드별로 확장(`CLAUDE_PLUGIN_ROOT`).
5. **(신규) 비충돌 네임스페이스**: Code 컴포넌트는 `tss-*`/`threat-scan*`로 네임스페이스하여 기존 전역 스킬/에이전트와 충돌하지 않는다.

## 완료 정의 (Definition of Done)

- [ ] `agents/tss-*.md` 15개 존재 — frontmatter(name/description/model/tools) 유효, 본문은 해당 SKILL.md 참조.
- [ ] `commands/threat-scan.md`(전체 스캔)·`threat-scan-html.md`(JSON→HTML)·`threat-scan-help.md`(안내) 존재.
- [ ] `skills/threat-scan-orchestrator/SKILL.md`에 frontmatter + `allowed-tools: Agent(tss-...)` 오케스트레이션, 본문 방법론은 보존.
- [ ] Desktop계열 13개 SKILL.md에 frontmatter(name/description) 추가, 본문 불변.
- [ ] `scripts/generate_html_report.py`가 `CLAUDE_PLUGIN_ROOT/dictionary` 경로 후보를 해석(repo·dist 기존 경로 회귀 없음).
- [ ] `.claude-plugin/plugin.json`·`marketplace.json` 존재 — 로컬 `/plugin marketplace add <path>`로 설치 가능.
- [ ] 레거시 `securityreports-*` 5개에 deprecated 표기 + `/threat-scan` 안내.
- [ ] `.claude/settings.local.json`에 `python3 scripts/*.py` 실행 허용.
- [ ] `VERSION` = 2.3.0.
- [ ] **Desktop 회귀 없음**: `bash build_claude_desktop.sh` 성공, zip 구성 종전과 동일.

## Phase 구성

| Phase | 문서 | 내용 |
|-------|------|------|
| 1 | `phase-1-agent-set.md` | `agents/tss-*.md` × 15 (frontmatter·SKILL.md 참조 본문·모델 배정) |
| 2 | `phase-2-commands.md` | `commands/threat-scan{,-html,-help}.md` |
| 3 | `phase-3-script-and-frontmatter.md` | 스크립트 `CLAUDE_PLUGIN_ROOT` 경로 + 오케스트레이터/Desktop계열 SKILL.md frontmatter |
| 4 | `phase-4-plugin-manifest-and-deprecation.md` | 플러그인 매니페스트 + 레거시 deprecated + settings/VERSION |
| 5 | `phase-5-validation.md` | E2E·오케스트레이션·HTML·Desktop 회귀·레거시 검증 |

## 범위 밖 (향후 버전)

- **플러그인 배포 패키징**: 버전드 zip 릴리스, 마켓플레이스 게시, 플러그인용 INSTALL.md, `build_claude_code_plugin.sh`.
- 레거시 `securityreports-*` 파이프라인의 v2.1 통합/마이그레이션.
- 신규 `--profile`(it-staff/dev/advanced) HTML 템플릿.
