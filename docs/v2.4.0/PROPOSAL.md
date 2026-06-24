# v2.4.0 오케스트레이션 재설계 — 제안서 (검토용)

> 상태: **제안 (미구현)**. 사용자 검토·수정 후 GOAL.md + phase 문서로 확정한다.
> 대상 버그: 병렬 분석 단계에서 ① Write 권한 hang, ② source-handler 미종료 인상,
> ③ 다음 단계 미진행(stuck). 근본 원인은 **서브에이전트 권한 게이트 + 오케스트레이터 블로킹 모델**.

---

## 1. 결정적 제약 (Claude Code 네이티브 동작 — 공식 문서 확인)

| # | 제약 | 출처/근거 | 설계 영향 |
|---|------|-----------|-----------|
| C1 | **서브에이전트 Write가 미승인 경로에 접근하면 권한 게이트에 걸린다.** 비대화형(헤드리스)에서는 hang, 대화형에서는 프롬프트/에러. | Agent SDK permissions 문서 | 서브에이전트 Write를 쓰려면 경로가 **사전 승인**되어야 한다. 플러그인은 권한 기본값을 배포할 수 없음(`agent`·`subagentStatusLine` 키만 지원). |
| C2 | **한 메시지로 N개 에이전트를 병렬 호출하면, N개가 전부 끝나야 결과가 한꺼번에 돌아온다.** 오케스트레이터는 그동안 블로킹된다. | Agent SDK subagents 문서 | "실행 중 라이브 모니터링/카운트"는 **오케스트레이터 차원에서 불가능**. 배치 종료 후에만 처리 가능. |
| C3 | **병렬 배치 중 1개가 hang하면 배치 전체가 무한 대기**, 오케스트레이터는 제어권을 못 받는다. | 동일 | hang은 "탐지"가 아니라 **사전 예방**해야 한다. 일단 hang되면 오케스트레이터가 개입할 방법이 없다. |
| C4 | **SubagentStop 훅은 각 서브에이전트가 끝날 때마다 개별 발화**한다(배치 종료 전에도). | Hooks 문서 | 배치 진행 중 "완료 로그"는 **훅으로만** 가능(오케스트레이터는 여전히 블로킹). |

**핵심 결론:** 요청하신 "오케스트레이터가 진행 중 모니터링하고 무응답을 탐지"는 *실행 중*에는 네이티브로 불가능하다(C2·C3). 대신 아래 3계층으로 **동등한 효과**를 비용 효율적으로 구성한다.

---

## 2. 제안 아키텍처 — "파일=진실 + 3계층 장애 방어"

### 설계 원칙: **완료 신호 = 출력 파일의 존재·유효성** (리턴 메시지가 아님)

리턴 메시지는 유실·오해(이전 "stray notification" 버그)·무응답 종료에 취약하다.
**각 에이전트의 OUTPUT_PATH 파일이 존재하고 JSON이 유효하면 = 완료**로 판정한다.
이것이 "리턴 없이 종료되는 fallback 탐지"의 가장 견고한 구현이다.

### 계층 ①: Phase 0' — 환경 적정성 검증 + 권한 사전 프로브 (NEW)

오케스트레이터가 배치 *이전에* 값싸게 환경을 확정한다:

```bash
# 1. SCAN_TMP 생성 (크로스플랫폼 깔끔한 이름 — -t 플래그 버그 회피)
SCAN_TMP=$(mktemp -d "${TMPDIR:-/tmp}/tss.XXXXXXXX")
# 2. 쓰기 가능 검증
touch "$SCAN_TMP/.probe" && rm "$SCAN_TMP/.probe" || echo "FAIL: SCAN_TMP not writable"
# 3. 필수 도구 검증
command -v git >/dev/null  || echo "FAIL: git missing"
command -v python3 >/dev/null || echo "FAIL: python3 missing"
```

그다음 **단 1개의 경량 프로브 서브에이전트(haiku)**를 띄워 `$SCAN_TMP/.agent-probe.json`에
한 줄 JSON을 Write하게 한다. 복귀 후 파일 존재를 확인:

- 파일 있음 → 서브에이전트 Write 정상. 8개 배치 진행 안전.
- 파일 없음/프로브 무응답 → **권한 미설정**. 8개 배치를 띄우기 전에 중단하고,
  추가해야 할 정확한 allow-rule을 사용자에게 안내한다.

> 이 프로브 1개가 "8개 배치가 통째로 hang"하는 최악의 비용을 막는다. (C3 예방)

### 계층 ②: Phase 1 — 병렬 분석 + 배치 후 체크포인트 (Bash)

- 8개 분석 에이전트를 **한 메시지로 병렬** 호출(사용자 요구 = 병렬 기준).
- 각 에이전트: `tools: Read, Write`. 자기 OUTPUT_PATH에 직접 Write 후 짧은 신호 리턴.
- 배치 복귀 후 **순수 Bash 체크포인트**(LLM 비용 0):

```bash
for step in step1 step2 ... step8; do
  f="$SCAN_TMP/$step.json"
  if   [ ! -f "$f" ];                                    then echo "$step: MISSING"
  elif ! python3 -c "import json;json.load(open('$f'))"; then echo "$step: INVALID"
  else echo "$step: OK ($(python3 -c "...; print(_meta.findings)"))"
  fi
done
```

- 상태표 출력: 에이전트별 OK / MISSING / INVALID + findings 카운트.
- **유한 재시도(1회):** MISSING/INVALID 에이전트만 타깃 재호출 → 재체크포인트.
- **장애 처리:** 1회 재시도 후에도 실패 → 어떤 에이전트가 왜 실패했는지 보고하고
  정책에 따라 (기본) **중단**. 보안 스캔은 완전성이 중요하므로 부분 진행을 기본값으로 두지 않는다.
- **라우팅:** 8개 파일 전부 OK일 때만 Phase 2로 진행.

### 계층 ③: SubagentStop 훅 — 완료 로깅 (선택, 라이브 가시성)

이미 `hooks/hooks.json`이 있으므로, matcher를 `tss-*`로 확장해 각 서브에이전트 종료 시
`$SCAN_TMP/progress.log`에 `<agent> stopped @ <ts>` 한 줄을 남긴다.
오케스트레이터는 블로킹 중이라 이를 *실시간 출력*하진 못하지만, 사용자는 훅 출력으로
배치 진행을 엿볼 수 있고, 배치 후 체크포인트가 이 로그도 함께 요약한다.

---

## 3. Phase 2/3 — 파일 라우팅 (순차)

다운스트림(relationship-graph·model-validity·deepdive·merger·translator)은
SCAN_TMP의 이전 단계 파일을 Read → 자기 출력 Write → 동일 체크포인트 패턴.
각 단계 사이에 동일한 "파일=진실" 검증을 적용한다.

---

## 4. 방법론 선택 근거 (비용 대비 효과)

| 후보 | 적합성 | 판정 |
|------|--------|------|
| **Workflow 도구** | 폴링·타임아웃·장애처리가 내장된 결정론 스크립트 | ❌ 메인 세션 전용·사용자 opt-in 필요. **배포 플러그인 런타임에서 사용 불가.** |
| **Task(단일 에이전트)** | 단순 | ❌ 13단계 파이프라인엔 부적합. |
| **Skill 오케스트레이터 + Agent + Bash 체크포인트** | 이식성·결정론·비용 | ✅ **채택.** Workflow의 장애처리·라우팅을 Bash 체크포인트로 이식. LLM 비용 0의 결정론 검증. |
| **SubagentStop 훅** | 배치 중 완료 로깅 | ✅ 보조 채택(계층 ③). |

**비용 효율 핵심:** 환경 검증·체크포인트·재시도 판정은 전부 **결정론 Bash**(LLM 토큰 0).
LLM은 실제 분석에만 사용. 프로브 1개(haiku)로 최악의 hang 비용을 예방.

---

## 5. 정직한 한계 (검토 시 인지 필요)

1. **실행 중 라이브 모니터링은 불가**(C2). "배치 후 체크포인트 + 사전 프로브 + 훅 로그"가 등가 대체.
2. **진짜 hang은 사후 탐지 불가**(C3). 사전 프로브 + 권한 문서화로 *예방*한다.
3. **서브에이전트 Write 권한**은 플러그인이 자동 부여 못 함(C1). INSTALLATION에 allow-rule을
   문서화하고, Phase 0' 프로브가 미설정을 조기 검출한다. (대화형 세션에서 실제로 프롬프트가
   뜨는지/에러로 떨어지는지는 **테스트로 확정** 필요 — 이 한 가지가 남은 불확실성.)

---

## 6. 확정 시 변경 범위 (참고)

| 계층 | 파일 |
|------|------|
| Code 오케스트레이터 | `skills/threat-scan-orchestrator/SKILL.md` (Phase 0' 프로브·체크포인트·재시도·라우팅) |
| Code 에이전트 | `agents/tss-*.md` (Write 유지 + OUTPUT_PATH 계약 명확화) |
| 훅 | `hooks/hooks.json` (matcher `tss-*` 완료 로깅), `scripts/` 로깅 스크립트 |
| 문서 | `docs/INSTALLATION.md` (allow-rule 안내), `CLAUDE.md` (패턴 갱신) |
| 버전 | `VERSION`·`plugin.json`·`threat-scan-help`·`CHANGELOG` → 2.4.0 |
| Desktop | **무변경** (Dual-Mode 무영향 — Desktop은 단일 컨텍스트라 이 문제 없음) |

---

## 7. 검토 요청 포인트

- [ ] **A. "파일=진실" 원칙** 채택 동의? (완료 판정을 리턴이 아닌 출력 파일로)
- [ ] **B. Phase 0' 프로브 에이전트 1개** 추가 동의? (배치 hang 예방 비용 ↔ 1 haiku 호출)
- [ ] **C. 병렬 유지 + 배치 후 체크포인트** vs 순차 라이브 진행 — 어느 쪽?
      (병렬=빠름·요약 카운트 / 순차=느림·실시간 카운트. C2 때문에 병렬에선 실시간 불가)
- [ ] **D. 장애 시 기본 정책** = 중단(완전성 우선) vs 부분 진행 — 어느 쪽?
- [ ] **E. SubagentStop 완료 로깅 훅**(계층 ③) 포함 여부?
- [ ] **F. allow-rule 문서화 + 프로브 조기검출** 방식 동의? (플러그인이 권한 자동부여 불가하므로)
