# Phase 2 — AI 구성요소 스캔범위 게이트 + 권한 사전등록 (dual-mode)

## 목표

① 스캔 대상 안에 `.claude/` 같은 **AI 도구 자체의 구성요소**(개발 지침·프롬프트·권한 구성)가
발견되면 스캔 포함 여부를 사용자에게 **정확히 1회** 묻는 게이트를 양 모드에 추가한다
(근거: [issues/TS-2.5.0-patch1.md](issues/TS-2.5.0-patch1.md) PART 3).
② Claude Code 완전 무정지 진행을 위해 스캔 전 1회 실행하는 **`/threat-scan-setup`** 커맨드로
프로젝트 권한 allow 규칙을 사전 등록한다(사용자 확정 — SecurityScanCode `securityscan-init` 선례).

## 2-A. 오케스트레이터 Phase 0(d) — AI 구성요소 스캔범위 확인 게이트

**파일:** `skills/threat-scan-orchestrator/SKILL.md`

### Code Plugin 섹션

1. `allowed-tools`에 `AskUserQuestion` 추가 — **이 게이트에서만 사용**, 다른 곳 사용 금지 명시.
2. AUTONOMOUS-COMPLETION CONTRACT(Phase 1에서 신설)에 **유일한 예외** 명시:
   이 질문 1회만 예외이며, 답을 받은 즉시 재질문 없이 Phase 5까지 완주.
3. **Phase 0(d) 신설** — Phase 0(c) nested-root 해석 직후, Phase 1 병렬 분석 직전:
   - `RESOLVED_TARGET_ROOT` 하위를 Python `os.walk`(Bash 결정론 스니펫)로 순회:
     - 탐지 대상 디렉터리: `.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `agents/`, `prompts/`
     - 탐지 대상 파일: `AGENTS.md`, `SKILL.md`, `.mcp.json`, `mcp.json`, `copilot-instructions.md`
     - 제외: `node_modules/`, `.git/`, `.next/`, `dist/`, `build/`, `vendor/`
   - **미발견(`NONE`) → 질문 없이 조용히 진행** (일반 프로젝트는 게이트를 인지하지 못함).
   - **발견 → `AskUserQuestion` 정확히 1회**: "AI 에이전트 구성요소가 발견되었습니다.
     스캔 범위에 포함할까요?" — 옵션: "포함 (권장)" / "제외".
   - **제외 선택 시**: 발견 경로 목록을 `EXCLUDE_PATHS`로 Phase 1 전체 분석 에이전트 프롬프트에
     전달 — "이 경로들은 존재만 인지하고 내용 분석 금지". 다른 카테고리 분석은 정상 수행.
   - 어느 쪽이든 `repository_summary.ai_agent_scope`에 `"included"`/`"excluded"` 기록
     (repo-indexer 프롬프트에 지시 — Schema V1.4 optional 필드, Phase 3에서 등재).

### Desktop 섹션

동일 방법론을 **대화 질의**로 서술 (Desktop에는 AskUserQuestion 도구 없음):
- 단계 1 인덱싱 결과에서 위 목록의 AI 구성요소를 확인.
- 발견 시 사용자에게 대화로 1회 질문(포함/제외), 답변 후 재질문 없이 완주.
- `ai_agent_scope` 기록 동일.
- ⚠️ Code 전용 표현(`AskUserQuestion`·`EXCLUDE_PATHS` 파라미터명·tss-*)을 Desktop 섹션에
  쓰지 않는다(BUG-02). 서술형으로.

## 2-B. 권한 자동 셋업 — 오케스트레이터 내장 + `/threat-scan-setup` 수동 경로

> **설계 (사용자 확정)**: 사용자가 setup을 직접 호출할 필요 없음. `/threat-scan` 시작 시
> 오케스트레이터가 **권한 규칙 부재를 감지하면 자동으로 셋업을 인라인 수행**한다.
> 이때 `.claude/settings.local.json`에 대한 Write가 권한 프롬프트를 **정확히 1회** 발생시키고,
> 사용자가 승인하면 규칙이 등록되어 이후 전 과정이 무정지로 진행된다.
> 가능 근거: 오케스트레이터는 메인 루프에서 실행되는 스킬이라 대화형 권한 프롬프트에
> 사용자가 응답할 수 있다(서브에이전트와 달리 hang 없음).

### (1) 오케스트레이터 Phase 0'' — 권한 자동 셋업 (Phase 0' 환경검증 직후)

**파일:** `skills/threat-scan-orchestrator/SKILL.md` Code 섹션

1. **감지 (결정론 Bash, 프롬프트 발생 없음):** 프로젝트 `.claude/settings.local.json`에서
   tss 규칙 존재 여부 확인:
   ```bash
   grep -q 'tss\.\*' .claude/settings.local.json 2>/dev/null && echo "PERMS OK" || echo "PERMS MISSING"
   ```
2. **`PERMS OK` → 무동작 통과** (재스캔·이미 셋업된 프로젝트는 프롬프트 0회).
3. **`PERMS MISSING` → 인라인 셋업:**
   - 기존 `settings.local.json`을 Read(없으면 새 구조 생성).
   - `permissions.allow`에 아래 규칙 **병합**(기존 항목 보존·중복 제거·덮어쓰기 금지) 후 Write.
     이 Write가 **사용자 확인·승인 1회**를 발생시킨다 — 승인 다이얼로그 자체가 동의 절차.
   - Write 완료 후: "권한 규칙 N건 등록 — 이후 무정지 진행" 1줄 보고하고 계속 진행.
   - **거부 시**: 등록 없이 진행하되, 이후 각 단계에서 개별 권한 프롬프트가 뜰 수 있음을
     1줄 안내(중단하지 않음 — 승인 여부는 사용자 선택).
4. **등록 규칙 (필요 최소셋 — 구현 시 파이프라인 실제 명령과 대조 확정):**
   ```json
   [
     "Write(/tmp/tss.*/**)",
     "Write(//var/folders/**/tss.*/**)",
     "Write(//private/var/folders/**/tss.*/**)",
     "Write(*/scanreport-*.json)",
     "Write(*/scanreport-*.html)",
     "Bash(mktemp:*)",
     "Bash(git clone:*)",
     "Bash(python3:*)",
     "Bash(ls:*)",
     "Bash(test:*)",
     "Bash(wc:*)",
     "Bash(rm -rf /tmp/tss.*)"
   ]
   ```
   `rm -rf`는 SCAN_TMP 정리 한정 패턴만 — 광범위 패턴 금지.
5. **AUTONOMOUS-COMPLETION CONTRACT 예외 갱신**: 허용되는 사용자 상호작용은 정확히 2가지 —
   ① 이 셋업 Write 승인(권한 규칙 부재 시 1회), ② Phase 0(d) AI 구성요소 게이트 질문(발견 시 1회).
   그 외 재질문·중간확인 금지.
6. **효력 검증은 기존 Phase 0(b) 프로브가 담당**: 셋업 직후 `tss-repo-indexer` Write 프로브가
   규칙 적용을 실증한다. 셋업했는데도 PROBE FAIL이면(설정 반영이 세션 재시작을 요구하는
   런타임 케이스) "설정은 등록됨 — 새 세션에서 /threat-scan 재실행" 안내 후 중단.
   **구현 시 실측 필수**: 같은 세션 내 신규 allow 규칙 즉시 적용 여부.

### (2) `/threat-scan-setup` 커맨드 (수동 경로 — 존치)

**파일:** `commands/threat-scan-setup.md` (신규)

- 위 (1)의 3–4와 동일한 병합 로직을 스캔 없이 단독 수행. 사전 셋업을 원하는 사용자·
  CI 준비용. 등록 결과 보고(추가/기존/파일 경로).
- 오케스트레이터와 커맨드가 **동일한 규칙 목록을 공유**해야 함 — 규칙 목록은
  오케스트레이터 SKILL.md에 정본을 두고 커맨드는 그것을 참조(중복 정의 금지, 드리프트 방지).

주의: `settings.local.json`은 gitignore 대상(`.claude/`)이므로 커밋되지 않는 로컬 설정 — 의도된 동작.

## 2-C. 연결 문서 갱신

- `commands/threat-scan.md`: "권한 규칙이 없으면 시작 시 자동으로 1회 승인을 요청합니다" 1줄.
- `commands/threat-scan-help.md`: 커맨드 표에 `/threat-scan-setup` 행 추가(설명: "권한 사전등록 —
  선택사항, 스캔 시 자동 수행됨").
- `INSTALLATION.md` "권한 설정" 절: **기본 = 자동(첫 스캔 시 1회 승인)**, 사전 등록을 원하면
  `/threat-scan-setup`, 수동 settings.json 편집은 최후 대안.
- 오케스트레이터 Phase 0(b) PROBE FAIL 안내문: Phase 0'' 자동 셋업과 연동된 문구로 교체
  (위 (1)-6 참조).

## 완료 조건 (검증 가능)

- [ ] 오케스트레이터 Code 섹션에 Phase 0''(권한 자동 셋업) + Phase 0(d)(게이트) 존재,
      `allowed-tools`에 AskUserQuestion, AUTONOMOUS CONTRACT에 상호작용 예외 2건 명시.
- [ ] 규칙 부재 프로젝트에서 `/threat-scan` 시작 → Write 승인 1회 → settings.local.json에
      규칙 병합 → 이후 무정지 완주 (실측).
- [ ] 규칙 존재 프로젝트에서 재실행 → 프롬프트 0회 통과 (실측).
- [ ] 같은 세션 내 신규 allow 규칙 즉시 적용 여부 실측 — 미적용 케이스면 (1)-6 폴백 문구 검증.
- [ ] 탐지 스니펫 실측: AI 구성요소 있는 대상 → 발견 목록 / 없는 대상 → `NONE`.
- [ ] Desktop 섹션에 대화 질의 서술 존재 + Code 전용 명칭 0건(BUG-02 diff 검증).
- [ ] `commands/threat-scan-setup.md` 존재(수동 경로), 병합 시 기존 규칙 보존.
- [ ] help 커맨드 표·threat-scan 도입부·INSTALLATION에 자동 셋업 반영.
