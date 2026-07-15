# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Desktop 배포 패키지 빌드 (zip 생성)
bash build_claude_desktop.sh

# 빌드 결과 검증 (frontmatter 스트리핑·경로 치환 확인)
unzip -l threat-scan-security.zip
grep -c "MASKING CONTRACT" dist_claude_desktop/threat-scan-security/references/sub-skills/sensitive-pattern-matcher.md
grep -c "tss-" dist_claude_desktop/threat-scan-security/SKILL.md  # 0 이어야 함 (Code 전용명 오염 확인)

# HTML 리포트 단독 재생성
python3 scripts/generate_html_report.py <report.json> --lang ko

# 버전 정합성 확인
cat VERSION
grep '"version"' .claude-plugin/plugin.json
grep "VERSION=" build_claude_desktop.sh | head -1
```

## Dual-Mode 아키텍처

이 리포지토리는 **Claude Desktop 스킬**과 **Claude Code 플러그인**을 동시에 지원한다.

```
skills/*/SKILL.md          ← 단일 원천 (방법론·스키마) — 양 모드 공유
agents/tss-*.md            ← Claude Code 전용 워커 (SKILL.md를 참조, 복제하지 않음)
commands/threat-scan*.md   ← Claude Code 진입점
.claude-plugin/            ← 플러그인 메타 (plugin.json, marketplace.json)
build_claude_desktop.sh    ← Desktop zip 빌드 (dist_claude_desktop/ 생성)
dictionary/                ← 번역 사전·HTML 템플릿 (양 모드 공유)
scripts/                   ← generate_html_report.py (양 모드 공유)
```

**기능 변경 시 반드시 두 계층을 함께 수정해야 한다.** 한쪽만 바꾸면 모드 간 동작이 불일치한다.

| 변경 대상 | 수정 파일 |
|-----------|-----------|
| 분석 방법론 | `skills/<name>/SKILL.md` (양 모드 자동 반영) |
| Code 파이프라인 단계 추가/삭제 | `agents/tss-*.md` 추가/삭제 + 오케스트레이터 `allowed-tools` 갱신 |
| Desktop 파이프라인 | `skills/threat-scan-orchestrator/SKILL.md` → `## 실행 절차 — Claude Desktop` 섹션 |
| 버전 범프 | `VERSION` · `.claude-plugin/plugin.json` · `commands/threat-scan-help.md` · `CHANGELOG.md` |

## 오케스트레이터 구조 — 알아야 할 핵심

`skills/threat-scan-orchestrator/SKILL.md`는 한 파일에 **두 모드의 실행 절차**가 공존한다.

- `## 실행 절차 — Claude Code Plugin` — Code 전용. `$SCAN_TMP` 파일 라우팅·체크포인트·`tss-*` 에이전트 이름.
- `## 실행 절차 — Claude Desktop` — Desktop 전용. `@sub-skill` 형식.

Code Plugin 섹션을 수정할 때 Desktop 섹션을 오염시키면 **BUG-02(Dual-mode 교차 오염)**가 재발한다. 두 섹션의 경계를 지킬 것.

**Desktop parity (v2.5.1 — TS-2.5.1 재발 방지):** Desktop은 결정론 강제를 단계 0(`enumerate_tree.py` 파일 열거)과 단계 11(`validate_report_schema.py` + `validate_compliance_tags.py` 게이트)에서 수행한다. 스키마·계약을 바꿀 때는 오케스트레이터 **공유부의 단계별 출력 계약 카드와 스키마 참조 목록을 반드시 함께 갱신**할 것 — v2.5.0에서 Code만 강화하고 Desktop 앵커(스키마 V1.3 잔존·번역 규칙 역전)를 갱신하지 않아 Desktop 품질 회귀(TS-2.5.1)가 발생했다. Code 한쪽만 강화하면 Desktop이 조용히 드리프트한다.

**오케스트레이터가 에이전트(Agent)가 아니라 스킬(Skill)인 이유:** Claude Code에서 서브에이전트는 다른 서브에이전트를 호출할 수 없다. 오케스트레이터를 스킬로 두고 `allowed-tools: Agent(tss-*)` frontmatter로 워커를 구동하는 패턴이 올바르다.

### 장애 방어 모델 (v2.4.0 / v2.5.0 — 반드시 이해할 것)

Agent 실행 모델은 런타임에 따라 다르다: 일부는 `Agent(tss-*)`를 blocking으로 처리하고,
일부는 async(백그라운드)로 실행해 즉시 "실행 중"만 반환한다(v2.4.1 실측 확인). 따라서
완료 판정을 리턴 메시지에 의존하지 않고 3계층으로 장애를 방어한다:

| 계층 | 구현 | 목적 |
|------|------|------|
| ① 사전 프로브 | Phase 0(b): `tss-repo-indexer` 1개를 병렬 배치 전에 먼저 호출 | 서브에이전트 Write 권한을 값싸게 검증 → 8개 통째 hang 예방 |
| ② 배치 후 체크포인트 | Phase 1 복귀 후 순수 Bash로 파일 존재·JSON유효·`_meta` 검증 | **파일=진실**. MISSING/INVALID는 1회 재시도 후 실패 시 **중단** |
| ③ 완료 로깅 훅 | `hooks/hooks.json` matcher `tss-.*` → `scripts/log_completion.sh` | 각 종료를 `progress.log`에 기록(가시성) |

**핵심 원칙 — 파일=진실:** 완료 판정은 에이전트의 리턴 메시지가 아니라 **OUTPUT_PATH 파일의
존재·유효성**이다. 리턴 유실·오해·무응답 종료에 견고하다.

**Monitor 정책 (v2.5.0 개정):** Agent가 async로 반환되면 `Monitor`(`until [ -f <OUTPUT_PATH> ]; do sleep N; done`)로
**OUTPUT_PATH 파일 출현을 대기하는 용도로만 허용**한다 — 완료 신호 수신 수단이지 폴링 남용이 아니다.
스톨 복구용 `TaskStop`도 허용. 그 외 불필요한 폴링 루프는 금지. (BUG-05 이력은 "Monitor 파라미터
오용 금지"로 재해석 — 잘못된 인자로 호출하지 말 것.)

**자율 완주 (v2.4.1-auto):** 스캔 시작 후 사용자에게 확인·질문하지 않고 Phase 5까지 완주한다.
유일한 예외는 Phase 0(d) AI 구성요소 게이트 질문 1회 + Phase 0'' 권한 셋업 승인 1회(규칙 부재 시).

## 에이전트 패턴

각 `agents/tss-*.md`는 방법론을 복제하지 않는다. 표준 패턴 (v2.3.5+):

```markdown
---
name: tss-<name>
model: sonnet              # 분석 워커: sonnet, 기계적 작업: haiku, 고난도 트리아지: opus
tools: Read, Write, Glob, Grep   # 분석 워커는 읽기전용 탐색(Glob/Grep) 포함. 셸 허용은 source-handler·html-report만
---
1. Read `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`
2. Glob으로 TARGET_PATH 전체 트리 완전 열거(경로 추측 금지) → Grep으로 sink 탐색.
3. Apply to every discovered file.
4. Write Schema V1.4 JSON to OUTPUT_PATH (from prompt).
5. Return: `Wrote <OUTPUT_PATH>; <N> findings`
```

**Glob/Grep은 읽기 전용 탐색 도구**로 "단계 1–10 코드 실행 금지" 제약과 상충하지 않는다.
경로 추측으로 파일을 놓치던 커버리지 결함(reviewOS-security 스캔 실측)을 방지한다.

**에이전트가 스스로 Write하는 이유:** 오케스트레이터가 대용량 JSON을 수신·Write하면
컨텍스트 폭발이 발생한다(BUG-06). 에이전트가 직접 OUTPUT_PATH에 Write하면 오케스트레이터는
짧은 확인 메시지만 받고, 완료 판정은 **파일 존재**로 결정론적으로 수행한다(파일=진실).

> **권한 의존:** 서브에이전트 Write는 비대화형이라 미승인 경로에서 권한 게이트에 걸려 hang할 수
> 있다. Phase 0(b)의 `tss-repo-indexer` 프로브가 배치 전에 이를 검출하고, INSTALLATION의
> allow-rule 안내(`Write(/tmp/tss.*/**)` 등)로 무중단 실행을 보장한다. 이 모델을 바꾸지 말 것.

`${CLAUDE_PLUGIN_ROOT}`는 Claude Code 플러그인 런타임이 주입한다. 미설정 환경에서는 `skills/<name>/SKILL.md`로 폴백.

**LLM·셸 실행 경계 (v2.4.1 개정):**
- `tss-source-handler`(단계 0)·`tss-html-report`(단계 11): Bash·파일 생성 허용.
- **단계 10.5 조립 (`assemble_bilingual.py`)**: 분할 모드 한정으로 오케스트레이터가 직접 Bash 실행 — 결정론적 Python만, LLM 추론 없음. 단계 0·11과 동일 성격의 결정론·셸 허용 예외.
- `tss-*` 분석 워커 (단계 1–10): `tools: Read, Write` — Bash 실행 금지, OUTPUT_PATH Write만 허용.
- Desktop 서브스킬(`skills/*/SKILL.md`): 파일 생성 없음 (Desktop 샌드박스 호환 — 별도 계층).

## Desktop 빌드 동작

`build_claude_desktop.sh`가 하는 일:

1. `skills/threat-scan-orchestrator/SKILL.md`에서 YAML frontmatter(`---...---`)를 `awk`로 스트리핑 → Desktop SKILL.md에 Code 전용 `allowed-tools` 줄이 섞이지 않도록.
2. 나머지 `skills/*/SKILL.md`를 `references/sub-skills/<name>.md`로 복사 후 상대 경로(`../../docs/` → `../docs/`) 치환.
3. `dictionary/*.json`, `dictionary/*.html`, `scripts/*.py`를 references에 복사.
4. `scripts/*.sh`는 복사하지 않음 — Code 전용 훅 스크립트가 Desktop dist에 들어가지 않도록 설계된 것.

## securityreports-* 스킬 상태

| 스킬 | 상태 | 이유 |
|------|------|------|
| `securityreports-sbom` | ✅ 활성 | Desktop 오케스트레이터 단계 8 + `tss-sbom` 원천 |
| `securityreports-deepdive` | ✅ 활성 | Desktop 오케스트레이터 단계 8.5 + `tss-deepdive` 원천 |
| `securityreports-scan/secrets/static/help` | ⚠️ deprecated | 구 SecurityScan 독립 진입점 — v2.1 오케스트레이터와 무관 |

Deprecated 스킬은 삭제하지 않고 유지 중(하위 호환).

## Schema V1.4 불변 규칙 (정본)

출력 JSON은 `docs/SCHEMA_V1.4_ENFORCEMENT.md`와 `docs/claude-threat-scan-json-schema-v1.4.md`를 따른다(정본). v1.3/v1.2 문서는 legacy 참조로 보존. **임의 필드 추가 금지** — `findings_summary`, `executive_summary`, `code_snippet`, 소문자 severity/verdict, 태그 금지 변형(`tags`/`kisa_tags`/`control_mapping` 등)은 스키마 위반이다.

**V1.4 추가(유일):** finding에 optional `compliance_tags`(KISA·AILLM·TA, regex `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$`, 0–4개, primary-first, EN/KO byte-identical) + `repository_summary.ai_agent_scope`(optional). 방출은 `docs/compliance-tagmap-distilled.md`(CTID-D), 검증은 `docs/compliance-tagging-deepdive.md`(CTID-V). enum 값(severity 등 13종)은 EN/KO 모두 영문 — 번역 금지(§9). 신규 optional 필드 추가 시 enforcement 문서도 함께 갱신한다.

## LLM·셸 실행 경계

- **단계 0(source-handler)·단계 11(html-report)**: 셸·파일 생성 허용.
- **단계 1–10**: 순수 Claude 추론만. 코드 실행·파일 쓰기 금지(Claude Desktop 샌드박스 호환 요건).

이 경계를 바꾸면 Desktop 호환성이 깨진다.
