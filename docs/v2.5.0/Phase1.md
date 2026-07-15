# Phase 1 — 파이프라인 자율완주·커버리지·번역 안정화 (patch1 PART1 upstream 반영)

## 목표

플러그인 캐시(2.4.1)에 적용·실측 검증된 patch1 PART1을 upstream repo에 반영한다.
근거: [issues/TS-2.5.0-patch1.md](issues/TS-2.5.0-patch1.md) PART 1 — 2026-07-15 재현 검증
(Phase 0–5 완주, 번역 조각 36–120초, parity-check 자동 복구 2건).

> **이식 원칙**: 캐시 `~/.claude/plugins/cache/threat-scan-security-marketplace/threat-scan-security/2.4.1/`에
> 검증된 구현본이 있다. 캐시본을 대조해 의미 동일하게 이식하고 재발명하지 않는다.
> 단, 캐시본에 이후 Phase(2·4)에서 다룰 변경(게이트·태깅)이 섞여 있다면 이 Phase 범위만 가져온다.

## 1-A. 분석 에이전트에 읽기 전용 탐색 도구 부여

**대상 (9개):** `agents/tss-repo-indexer.md`, `tss-static-analyzer.md`, `tss-binary-analyzer.md`,
`tss-skill-analyzer.md`, `tss-sensitive-patterns.md`, `tss-policy-verifier.md`,
`tss-prompt-optimizer.md`, `tss-sbom.md`, `tss-deepdive.md`

1. frontmatter: `tools: Read, Write` → `tools: Read, Write, Glob, Grep`
2. 본문 Rules에 추가:
   - "TARGET_PATH 하위 전체 트리를 Glob으로 **완전 열거**한 뒤 분석한다. 경로 추측 금지."
   - Glob/Grep은 읽기 전용 도구로 "단계 1–10 코드 실행 금지" 제약과 상충하지 않음을 주석.

**비대상:** `tss-relationship-graph`·`tss-model-validity`·`tss-report-merger`·`tss-translator`
(SCAN_TMP의 step 파일만 읽음 — 트리 탐색 불필요), `tss-source-handler`·`tss-html-report`(Bash 보유).

## 1-B. 번역기 ANTI-HANG + JSON-SAFETY (`agents/tss-translator.md`)

기존 Mode A/B(v2.4.1) 구조 위에 다음 계약을 추가:

1. **ANTI-HANG**: 영문 원문 재출력 금지. 담당 조각(`korean_report{}` 부분) 하나만 단일 Write.
   시작 즉시 Read→번역→Write→1줄 확인 반환(중간 사고 서술 금지).
2. **`ITEM_RANGE` 옵션**: 프롬프트에 `ITEM_RANGE: 0-8`(end-exclusive)이 오면 해당 카테고리
   배열의 그 슬라이스만 번역(대형 배열 재분할용 백스톱).
3. **JSON-SAFETY**: 값 문자열 내부에 원시 `"` 금지(홑따옴표·낫표·`\"` 사용), 개행·탭은
   `\n`/`\t` 이스케이프, 출력에 코드펜스(```) 금지.

※ enum 번역 금지 가드레일은 **Phase 4**에서 스킬 계층(`bilingual-translator/SKILL.md`)과 함께 반영.

## 1-C. 오케스트레이터 자율완주 + 자가 복구 (`skills/threat-scan-orchestrator/SKILL.md` — Code 섹션만)

1. **AUTONOMOUS-COMPLETION CONTRACT** (Code 섹션 최상단 노트):
   시작 후 사용자 확인 없이 Phase 5까지 완주한다. 하드 실패(환경검증 FAIL·PROBE FAIL·
   재시도 후 체크포인트 실패)에서만 중단. ※Phase 2에서 게이트 질문 1회가 유일한 예외로 추가됨.
2. **Monitor 정책 개정** (사용자 확정):
   - `allowed-tools`에 `Monitor, TaskStop` 추가.
   - 완료 판정 = OUTPUT_PATH 파일(불변). Agent 호출이 async로 반환되면
     `Monitor`(command: `until [ -f "<OUTPUT_PATH>" ]; do sleep 5; done` 형태, timeout 명시)로
     파일 생성을 대기한다. **Monitor는 이 용도로만 허용** — 그 외 폴링·백그라운드 대기 금지.
   - 기존 "⛔ Monitor 도구 절대 금지" 문구를 위 정책으로 교체.
3. **Phase 0(c) — nested-root 자동 하강**: repo-indexer 결과가 0-파일/empty면 매니페스트
   (package.json 등) 위치를 찾아 실제 루트로 하강 후 재인덱싱. `RESOLVED_TARGET_ROOT` 확정.
4. **Phase 3-B — 분할 번역 기본값 변경**: "카테고리당 조각 1개"가 기본(단일 카테고리 조각은
   30–120초에 안정 완료). `ITEM_RANGE` 슬라이싱은 최후 백스톱(경계 중복 리스크 주석).
   스톨 시 `TaskStop`으로 중단 후 재분할.
5. **Phase 3-C — 조립 강화**: 조립 전 조각별 JSON 유효성 검증(깨진 카테고리만 자동 재번역),
   조립은 `SCAN_TMP` 환경변수 + `assemble_bilingual.py`의 auto-glob 사용
   (zsh는 `--frags $(ls ...)` unquoted를 단어분할하지 않아 실패 — 실측 확인).
   조립 후 EN/KR 카테고리별 항목 수 parity 검증, 불일치 카테고리만 재번역.

**⚠️ Desktop 섹션(`## 실행 절차 — Claude Desktop`)은 이 Phase에서 무수정.** (BUG-02)

## 1-D. `CLAUDE.md` 정책 개정

1. "핵심 제약 — Monitor/폴링 금지" 절 → **"Monitor는 OUTPUT_PATH 파일 대기 용도로만 허용"**으로 개정:
   - Agent 실행이 async일 수 있음(실측), 완료 판정은 여전히 파일=진실.
   - BUG-05 이력은 "Monitor 파라미터 오용(잘못된 인자) 금지"로 재해석 주석.
2. 에이전트 패턴 표: `tools: Read, Write` → `tools: Read, Write, Glob, Grep`(분석 워커),
   "전체 트리 완전 열거" 원칙 1줄 추가.

## 완료 조건 (검증 가능)

- [ ] `grep -l "Glob, Grep" agents/tss-*.md | wc -l` = 9 (대상 9개 정확히).
- [ ] `agents/tss-translator.md`에 ANTI-HANG·ITEM_RANGE·JSON-SAFETY 절 존재.
- [ ] 오케스트레이터 `allowed-tools`에 Monitor·TaskStop 포함, "절대 금지" 구 문구 0건,
      AUTONOMOUS-COMPLETION CONTRACT·Phase 0(c)·3-B·3-C 개정 반영.
- [ ] Desktop 섹션 diff 0 (git diff로 `## 실행 절차 — Claude Desktop` 이후 무변경 확인).
- [ ] CLAUDE.md에 Monitor 신정책 반영, "Monitor 도구·백그라운드·폴링 루프를 쓰면 안 된다" 구 문구 제거.
- [ ] 캐시본 대비 의미 누락 없음: patch1 PART1의 A/B/C 항목별 대조 체크.
