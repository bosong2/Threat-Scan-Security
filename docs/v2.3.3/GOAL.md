# v2.3.3 — 마스터-서브에이전트 오케스트레이션 재설계

## 목표 (1문장)

Claude Code 플러그인의 오케스트레이터를 **얇은 컨텍스트의 master agent**로 재설계하여,
(1) 워커 산출물을 파일로 라우팅해 마스터에 **Opus**를 정당화하고, (2) 탐지 워커가
**raw secret을 절대 반환하지 않도록 계약을 강제**하며, (3) **SubagentStop 리댁션 훅**으로
출력을 결정론적으로 정화하고, (4) 모델·권한 차등과 **사후 효율 분석**을 도입한다.

## 배경

v2.3.2에서 오케스트레이터 조기 종료(BUG-01)는 "전부 반환될 때까지 기다린다" 지시로
해결됐다. 그러나 실사용에서 두 가지 구조적 문제가 남았다:

1. **출력 과다·비밀 노출** — Claude Code 모드에서 secret 스캔 결과의 키 값이 콘솔과
   오케스트레이터 컨텍스트로 새어 나온다. `tss-sensitive-patterns`에 "mask with `***`"
   **권고 문구는 있으나 강제되지 않으며**, 워커가 finding 증거에 raw 값을 담아 반환하면
   그대로 마스터 컨텍스트→콘솔로 전파된다.

2. **마스터가 수동 대기자** — 오케스트레이터가 8개+ 워커의 finding JSON 조각을 **전부
   자기 컨텍스트로 수신**해 다음 단계로 넘긴다. 컨텍스트가 비대해져 Opus를 두면 비싸고,
   호출 사이에 능동적 통제(검증·집계)도 없다.

### 핵심 사실 (Claude Code 실행 모델 검증, 2026-06-23)

| 사실 | 근거 | 설계 함의 |
|------|------|-----------|
| 오케스트레이터는 서브에이전트의 **최종 반환만** 받는다(중간 출력 미전달) | code.claude.com — Agent tool behavior | "실시간 모니터링"은 불가 → master 역할을 *호출 사이 통제*로 재정의 |
| 서브에이전트 중간 출력은 사용자 UI에도 미노출(자체 컨텍스트 격리) | Subagents docs | 비밀 노출은 **반환 계약** 문제이지 도구(Task) verbosity 문제가 아님 |
| `model`/`tools`/`disallowedTools` frontmatter로 에이전트별 모델·권한 하드 통제 가능 | Subagents docs | 탐지 워커는 `Read`만 → 유출·쓰기 구조적 차단 |
| 런타임 토큰 조회 API **없음**. 트랜스크립트(`subagents/agent-*.jsonl`) 사후 파싱만 | Tools reference | 효율 모니터링은 자기보고 메트릭 + 사후 분석으로 |
| **플러그인** 서브에이전트는 frontmatter `hooks`/`mcpServers`/`permissionMode` 미지원 | Subagents docs | 리댁션 훅은 플러그인 `hooks/hooks.json`(SubagentStop)에 둔다 |

### 비교 원천: SecurityScanCode

`SecurityScanCode`의 `securityscan-triage`는 이미 올바른 패턴을 구현했다:
- 산출물을 `$SCAN_TMP/received-*.json` **파일**로 라우팅 → 마스터는 제어 흐름 텍스트만 보유.
- secret-triage 에이전트는 `locator`(run/index)+verdict **JSON만** 반환, raw 값은 미반환.
- 호출 사이에 coverage 검증·merge·schema 검증을 Bash로 수행(능동적 master).

v2.3.3은 이 셋을 Threat-scan-security에 이식한다. (단, TSS는 엔진이 없는 LLM-only
탐지이므로 "엔진이 raw를 쥔다"는 SecurityScanCode식 분리는 불가 — 대신 **워커 반환 계약
+ SubagentStop 훅**의 2중 마스킹으로 동등한 효과를 낸다.)

## 설계 원칙

1. **데이터는 마스터 컨텍스트가 아니라 파일로 흐른다** — 마스터는 "경로 + 카운트 +
   verdict 집계"만 쥔다. 이로써 Opus 마스터가 토큰상 정당화된다.
2. **탐지 워커는 raw secret을 반환하지 않는다** — 마스킹된 값(`AKIA****`) + locator만.
   프롬프트 권고가 아니라 **반환 스키마 + 훅**으로 강제.
3. **master 역할 = 호출 사이의 통제** — 실시간 감시가 아니라 dispatch 전 계획, 수신 후
   검증·집계·정화.
4. **권한은 하드 allow-list** — 탐지 워커 `tools: Read`, 마스터만 `Bash`/`Write`.
5. **Dual-Mode 동시 수정** — 공유 방법론(`skills/*/SKILL.md`)은 양 모드 반영, Code 전용
   요소(파일 라우팅·훅·Opus)는 Claude Code 계층에만.

## 적용 범위 (Dual-Mode 계층 매핑)

| 변경 | Claude Code 계층 | Claude Desktop 계층 | Phase |
|------|------------------|---------------------|-------|
| 워커 반환 계약: 마스킹 + locator-only | `agents/tss-sensitive-patterns.md`, `tss-static-analyzer.md` | `skills/sensitive-pattern-matcher/SKILL.md`, `skills/static-code-analyzer/SKILL.md` (단일 원천) | 1 |
| 마스터 파일 라우팅 + Opus + Write 권한 | `skills/threat-scan-orchestrator/SKILL.md`(Code 절차), `commands/threat-scan.md` | 영향 없음(순차 단일 컨텍스트) | 2 |
| SubagentStop 리댁션 훅 | `hooks/hooks.json`(신설), `.claude-plugin/plugin.json`, `build_claude_desktop.sh` | 미적용(샌드박스) | 3 |
| 모델·권한 차등 정합성 + 효율 메트릭 자기보고 | `agents/tss-*.md` 전체 | `skills/*/SKILL.md` `_meta` 규약 | 4 |
| 버전 범프·빌드·검증 | `VERSION`, `plugin.json` | `build_claude_desktop.sh` | 5 |

## 완료 정의 (검증 가능)

- [ ] `/threat-scan <대상>` 실행 시 secret 키 **raw 값이 콘솔/JSON에 노출되지 않음**
      (마스킹된 형태 `AKIA****` + locator만).
- [ ] 오케스트레이터가 워커 산출물을 `$SCAN_TMP/*.json` 파일로 라우팅, 마스터 컨텍스트에
      finding 본문을 누적하지 않음.
- [ ] 오케스트레이터 `allowed-tools`에 `Write` 포함, 파일 라우팅 절차 명시.
- [ ] `hooks/hooks.json`에 `SubagentStop` 리댁션 훅 존재, `plugin.json`에 `hooks` 등록.
- [ ] 탐지 워커 frontmatter `tools: Read`(쓰기·셸 불가), 마스터 모델 `opus` 권장 명시.
- [ ] 각 워커 반환 JSON에 `_meta`(files_scanned/findings/depthReached) 자기보고 footer 포함.
- [ ] 스캔 후 트랜스크립트 기반 per-agent 효율 요약을 Phase 5 보고에 포함(선택적 산출).
- [ ] Desktop 빌드 성공, 공유 방법론(마스킹 계약)이 Desktop SKILL.md에도 반영, 회귀 없음.
- [ ] `VERSION` = 2.3.3, `plugin.json` version 2.3.3, CHANGELOG 갱신.

## Phase 구성

| Phase | 문서 | 내용 |
|-------|------|------|
| 1 | `phase-1-worker-return-contract.md` | 탐지 워커 마스킹 + locator-only 반환 계약 강제 (공유 방법론) |
| 2 | `phase-2-master-file-routing.md` | 마스터 파일 라우팅 + 얇은 컨텍스트 + Opus + Write 권한 |
| 3 | `phase-3-redaction-hook.md` | SubagentStop 리댁션 훅 신설 + plugin/build 등록 |
| 4 | `phase-4-model-permission-efficiency.md` | 모델·권한 차등 정합성 + 효율 메트릭 자기보고/사후 분석 |
| 5 | `phase-5-version-build-validation.md` | 버전 범프·빌드·E2E 검증·릴리스 |
