---
name: threat-scan-orchestrator
description: >
  Orchestrate the full Claude Threat Scan pipeline (단계 0–11) over a target
  skill/agent/plugin/repo and produce a bilingual JSON report plus a KO HTML
  report. Use when asked to scan, audit, or vet a repository for security threats.
allowed-tools: Agent(tss-source-handler), Agent(tss-repo-indexer), Agent(tss-static-analyzer), Agent(tss-binary-analyzer), Agent(tss-skill-analyzer), Agent(tss-relationship-graph), Agent(tss-model-validity), Agent(tss-sensitive-patterns), Agent(tss-policy-verifier), Agent(tss-prompt-optimizer), Agent(tss-sbom), Agent(tss-deepdive), Agent(tss-report-merger), Agent(tss-translator), Agent(tss-html-report), Bash, Read, Write, Monitor, TaskStop, AskUserQuestion
---

# Claude Threat Scan Orchestrator

Scan target: **$ARGUMENTS**

You orchestrate an 11-stage pipeline. **Do not terminate after spawning agents —
proceed through every phase and report only when Phase 5 is done.**

If `$ARGUMENTS` is empty, ask for a path / git URL / zip and stop.

---

## 실행 절차 — Claude Code Plugin

> 이 섹션은 Claude Code Plugin 모드 전용입니다. Claude Desktop은 아래
> **실행 절차 — Claude Desktop** 섹션과 **스캔 순서** 표를 따릅니다.

> ### 🤖 AUTONOMOUS-COMPLETION CONTRACT (v2.4.1-auto — 최우선)
> 스캔이 시작되면 **사용자에게 어떤 확인·질문도 하지 않고 Phase 5까지 자동 완주**한다.
> 사용자가 중간에 개입해야 하는 상황을 스스로 제거한다.
> **예외는 정확히 2가지**: ① Phase 0''의 권한 셋업 승인(규칙 부재 시 1회), ② Phase 0(d)의
> **AI 에이전트 구성요소 스캔 범위 확인**(대상 폴더에 `.claude/`, `.cursor/` 등 AI 에이전트 관련
> 구성요소가 존재할 때 스캔 포함 여부를 1회 질문 — v1.4.3). 답을 받은 즉시 다시 묻지 않고 완주한다.
> - **에이전트 실행 모델 불문:** 런타임이 `Agent(tss-*)`를 blocking으로 처리하든
>   async(백그라운드)로 처리하든, **완료 판정은 항상 OUTPUT_PATH 파일의 존재·유효성**이다.
>   async면 해당 파일이 나타날 때까지 대기한다(파일-appear 대기 목적의 `Monitor`
>   `until [ -f <OUTPUT_PATH> ]; do sleep N; done` 사용 허용 — 폴링 남용이 아니라 완료 신호 수신 수단).
> - **스톨 자동 복구:** 어떤 에이전트가 정해진 시간 안에 OUTPUT_PATH를 쓰지 못하고 무진전이면
>   (특히 단계 10 번역), 사용자에게 묻지 말고 **자동으로 중단(TaskStop)→더 잘게 분할→재호출**한다.
>   재분할·재시도는 이 문서의 각 Phase 복구 규칙을 따른다.
> - **하드 실패에서만 중단:** 환경 부적합(Phase 0'), 서브에이전트 Write 권한 실패(Phase 0(b) PROBE FAIL),
>   또는 1회 재시도·재분할 후에도 산출물이 없는 경우에만 원인을 명시하고 중단한다.
>   그 외에는 절대 멈추지 않는다.

> **모델 권장(v2.3.3):** 이 오케스트레이터는 finding 본문을 파일로 라우팅해
> 컨텍스트를 얇게 유지하므로 **Opus** 사용을 권장한다(라우팅·검증 판단력 ↑, 토큰 ↓).
> 워커 모델은 각 `agents/tss-*.md` frontmatter에 고정돼 있다.

> **⛔ Agent 호출 동작은 런타임에 따라 다르다:** 일부 런타임은 `Agent(tss-*)`를 blocking으로
> 처리해 반환까지 자동 대기한다 — 이때는 추가 대기 코드가 필요 없다. 그러나 async(백그라운드)로
> 실행하는 런타임에서는 즉시 "실행 중"만 돌아온다. **어느 경우든 완료 판정은 OUTPUT_PATH 파일**이며
> (아래 🎯), async면 파일 출현까지 대기한다. 이 목적의 `Monitor`(`until [ -f <path> ]` 대기)와
> 스톨 복구용 `TaskStop`만 허용하며, 그 외 불필요한 폴링 루프는 쓰지 않는다.

> **🎯 완료 판정 = 출력 파일(OUTPUT_PATH)의 존재·유효성.** 에이전트의 리턴 메시지가
> 아니라 **파일이 진실**이다. 리턴 메시지 유실·오해·무응답 종료에 견고하다.
> 각 Phase는 Bash 체크포인트로 파일을 검증한 뒤에만 다음 Phase로 라우팅한다.

### Phase 0' — 환경 적정성 검증 (Bash, 최초 1회)

> **핵심 원칙:** Bash 도구는 호출마다 새 쉘을 생성해 변수가 유지되지 않는다.
> 아래 출력값을 **컨텍스트에 기록**하고, 이후 모든 Write·Bash·Agent 호출에서
> `$변수` 대신 **실제 경로/값을 직접 대입**한다.

```bash
SCAN_TMP=$(mktemp -d "${TMPDIR:-/tmp}/tss.XXXXXXXX")   # 크로스플랫폼: X가 치환된 고유 경로
OUT_DIR=$(pwd)                                          # 최종 산출물 저장 위치 (실행 시점 고정)
TIMESTAMP=$(date +%Y%m%d%H%M%S)                        # 파일명 고유성 보장용
# 환경 적정성 검증
touch "$SCAN_TMP/.probe" && rm "$SCAN_TMP/.probe" && WJ=OK || WJ=FAIL
command -v git     >/dev/null && GIT=OK || GIT=FAIL
command -v python3 >/dev/null && PY=OK  || PY=FAIL
printf '\n=== TSS SESSION VALUES ===\nSCAN_TMP=%s\nOUT_DIR=%s\nTIMESTAMP=%s\nwritable=%s git=%s python3=%s\n=========================\n' \
  "$SCAN_TMP" "$OUT_DIR" "$TIMESTAMP" "$WJ" "$GIT" "$PY"
```

**출력 예시 (반드시 기록):**

```
=== TSS SESSION VALUES ===
SCAN_TMP=/var/folders/.../T/tss.a1b2c3d4
OUT_DIR=/Users/user/my-project
TIMESTAMP=20260623150000
writable=OK git=OK python3=OK
=========================
```

`writable`/`git`/`python3` 중 하나라도 `FAIL`이면 원인을 보고하고 **중단**한다.
이후 모든 경로에는 `$SCAN_TMP` 변수가 아닌 `/var/folders/.../tss.a1b2c3d4`처럼 **실제값**을 대입한다.

### Phase 0'' — 권한 자동 셋업 (무정지 진행 보장, v2.5.0)

> **목적:** 사용자가 `/threat-scan-setup`을 직접 호출하지 않아도, 권한 규칙이 없으면
> 오케스트레이터가 자동으로 프로젝트 `.claude/settings.local.json`에 규칙을 등록한다.
> 이 Write가 **사용자 확인·승인 1회**로 작동하고, 승인 후 전 과정이 무정지로 진행된다.
> (오케스트레이터는 메인 루프 스킬이라 권한 프롬프트에 사용자가 응답 가능 — 서브에이전트와 달리 hang 없음.)

**(1) 감지 (결정론 Bash — 프롬프트 없음):**

```bash
grep -q 'tss\.\*' .claude/settings.local.json 2>/dev/null && echo "PERMS OK" || echo "PERMS MISSING"
```

- **`PERMS OK` → 무동작 통과** (이미 셋업된 프로젝트·재스캔은 프롬프트 0회).
- **`PERMS MISSING` → 인라인 셋업 수행:**
  1. `.claude/settings.local.json`을 Read(없으면 `{"permissions":{"allow":[]}}` 신규 구조).
  2. `permissions.allow`에 아래 규칙을 **병합**(기존 항목 보존·중복 제거·덮어쓰기 금지) 후
     Write 도구로 저장한다. **이 Write가 사용자 승인 1회를 발생시킨다.**
  3. Write 성공 → "권한 규칙 N건 등록 — 이후 무정지 진행" 1줄 보고 후 계속.
  4. Write 거부 → 등록 없이 진행하되 "이후 각 단계에서 개별 권한 프롬프트가 뜰 수 있음" 1줄 안내
     (중단하지 않음 — 승인 여부는 사용자 선택).

**등록 규칙 (정본 — `/threat-scan-setup` 커맨드도 이 목록을 공유):**

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

> 효력 검증은 아래 Phase 0(b) Write 프로브가 담당한다. 셋업 직후에도 PROBE FAIL이면(신규 allow
> 규칙이 세션 재시작을 요구하는 런타임) "설정은 등록됨 — 새 세션에서 /threat-scan 재실행" 안내 후 중단.

### Phase 0 — 소스 준비 + 서브에이전트 Write 프로브 (단계 0 → 1)

**(a) 소스 준비:** `tss-source-handler` 에이전트를 호출한다.
**반환값(TARGET_PATH)을 받을 때까지** 다음으로 진행하지 않는다. Bash로 검증:

```bash
test -d "/actual/target/path" && echo "TARGET_PATH OK" || echo "FAIL: not a directory"
```

`FAIL`이면 보고 후 중단한다.

**(b) Write 프로브 겸 단계 1:** `tss-repo-indexer` **1개만 먼저** 호출한다(병렬 배치 이전).
이 에이전트가 OUTPUT_PATH에 Write에 성공하면 **서브에이전트 Write 권한이 정상**임이
확인된다 — 즉 repo-indexer가 권한 프로브를 겸한다(별도 비용 0, repo 인덱스는 어차피 필요).

프롬프트:
```
TARGET_PATH: /actual/target/path
OUTPUT_PATH: /var/folders/.../tss.a1b2c3d4/step1-repo-indexer.json
(repo 인덱싱 지시)
```

호출 복귀 후 Bash로 프로브 검증:

```bash
if [ -f "/var/folders/.../tss.a1b2c3d4/step1-repo-indexer.json" ]; then
  echo "PROBE OK: 서브에이전트 Write 정상 — 병렬 배치 진행"
else
  echo "PROBE FAIL: 서브에이전트가 파일을 쓰지 못함 (권한 규칙 미적용)"
  echo "→ Phase 0''에서 규칙을 등록했다면 새 세션에서 /threat-scan 재실행이 필요할 수 있습니다."
  echo "→ 규칙 미등록 상태라면 /threat-scan-setup 실행 후 재시도하세요."
fi
```

`PROBE FAIL`이면 **8개 병렬 배치를 띄우지 않고 중단**한다(통째 hang 예방).

**(c) 실제 프로젝트 루트 자동 해석 (0-파일 오탐 방지):** repo-indexer가 `total_files=0`
또는 "empty"를 보고하면 사용자에게 묻지 말고 **자동으로 중첩 루트를 탐색**한다. 아래 Bash로
매니페스트(`package.json`/`pyproject.toml`/`go.mod`/`Cargo.toml`/`pom.xml`/`.git`)의 실제 위치를
찾아 그 디렉터리를 새 `TARGET_PATH`로 삼고 **repo-indexer를 1회 재호출**한 뒤 진행한다.

```bash
T="/actual/target/path"
ROOT=$(python3 - "$T" <<'PY'
import os,sys
t=sys.argv[1]
marks={"package.json","pyproject.toml","go.mod","Cargo.toml","pom.xml","build.gradle",".git"}
# 최상위에 매니페스트가 있으면 그대로, 없으면 가장 얕은 매니페스트 보유 디렉터리로 하강
best=None;bestdepth=10**9
for dp,dns,fns in os.walk(t):
    dns[:]=[d for d in dns if d not in {"node_modules",".next","dist","build",".git","vendor"}]
    depth=dp[len(t):].count(os.sep)
    if marks & (set(fns)|set(dns)):
        if depth<bestdepth: best=dp;bestdepth=depth
print(best or t)
PY
)
echo "RESOLVED_TARGET_ROOT=$ROOT"
```

`RESOLVED_TARGET_ROOT`이 원래 경로와 다르면 그 값을 이후 모든 Phase의 `TARGET_PATH`로 사용한다.

**(d) AI 에이전트 구성요소 스캔 범위 확인 (신규 — v1.4.3, 유일한 사용자 질문 지점).**
`RESOLVED_TARGET_ROOT` 하위에 `.claude/`, `.cursor/`, `.github/copilot-instructions.md`,
`AGENTS.md`, `SKILL.md`, `.mcp.json`/`mcp.json`, `agents/**`, `prompts/**` 같은 **AI 에이전트/도구
구성요소**가 존재하는지 Bash로 탐지한다. 이 항목들은 프로젝트 소스코드가 아니라 사용자(또는 다른 팀)의
AI 도구 설정·프롬프트·권한 구성일 수 있어, 스캔 범위 포함 여부는 **사용자가 직접 결정해야 하는 사안**이다.

```bash
T="/actual/RESOLVED_TARGET_ROOT"
python3 - "$T" <<'PY'
import os, sys
t = sys.argv[1]
dir_names = {".claude", ".cursor", "agents", "prompts"}
file_names = {"AGENTS.md", "SKILL.md", ".mcp.json", "mcp.json", "copilot-instructions.md"}
found = []
for root, dns, fns in os.walk(t):
    dns[:] = [d for d in dns if d not in {"node_modules", ".git", ".next", "dist", "build", "vendor"}]
    rel = os.path.relpath(root, t)
    for d in list(dns):
        if d in dir_names:
            found.append((os.path.join(rel, d) if rel != "." else d) + "/")
    for f in fns:
        if f in file_names:
            found.append(os.path.join(rel, f) if rel != "." else f)
print("AI_AGENT_PATHS_FOUND:")
print("\n".join(sorted(set(found))) if found else "NONE")
PY
```

- **`NONE`이면 질문 없이 조용히 Phase 1로 진행**한다(해당 없는 대다수 프로젝트는 이 게이트를 인지하지 못함).
- **하나 이상 발견되면**, Phase 1 배치를 띄우기 **전에** `AskUserQuestion` 도구로 **정확히 1회** 사용자에게 묻는다:
  - 질문: "대상 폴더에서 AI 에이전트 관련 구성요소가 발견되었습니다: `<발견된 경로 목록>`. 이번 보안
    스캔 범위에 포함할까요?"
  - 옵션(권장 표시 포함):
    1. **포함(권장)** — 정상적으로 skill/policy 분석 대상에 포함(단계 4 `tss-skill-analyzer`,
       단계 6 `tss-policy-verifier`가 이미 이런 구성요소를 검사하도록 설계돼 있음).
    2. **제외** — 이 경로들을 스캔 대상에서 배제하고 애플리케이션 코드만 스캔.
  - 답을 받으면 **그 즉시 다시 묻지 않고** 나머지 Phase 5까지 자율 완주한다(위 AUTONOMOUS-COMPLETION
    CONTRACT의 유일한 예외가 여기서 소진됨).
- **제외를 선택한 경우:** Phase 1의 `tss-skill-analyzer`·`tss-policy-verifier`(및 필요 시 다른 분석
  에이전트) 프롬프트에 `EXCLUDE_PATHS: <발견된 경로 목록>`을 명시하고 "이 경로들의 내용을 읽거나
  분석하지 말 것(존재 여부만 무시)"이라고 지시한다. 단계 9 `repository_summary`에
  `ai_agent_scope: "excluded"`(포함 시 `"included"`) 필드를 함께 기록해 최종 리포트에서 이 결정이
  투명하게 드러나게 한다.
- **포함을 선택한 경우:** 별도 조치 없이 기존 설계대로 진행(경로 배제 안 함). `repository_summary`에
  `ai_agent_scope: "included"`만 기록.

### Phase 1 — 병렬 분석 (단계 2–8, **ONE message**, 7개 동시)

> repo-indexer(단계 1)는 Phase 0(b)에서 완료됐다. 여기서는 **나머지 7개를 한 메시지로 병렬** 호출한다.
> 완료 판정은 리턴이 아니라 **OUTPUT_PATH 파일**이다(파일=진실).

> **커버리지 (v2.4.1-auto):** 분석 에이전트는 이제 `Glob`/`Grep`로 대상 트리를 **직접 완전 열거**한다
> (경로 추측 금지). 각 프롬프트에 `TARGET_PATH`가 실제 프로젝트 루트인지 확인하고, 에이전트에
> "전체 트리를 Glob으로 열거해 모든 관련 파일을 빠짐없이 스캔하라"고 명시한다. 별도의 보충 스캔
> 패스를 수동으로 돌릴 필요가 없다 — 커버리지 미달은 체크포인트에서 자동 감지·재호출로 처리한다.

각 에이전트 프롬프트에 `TARGET_PATH` + `OUTPUT_PATH`를 명시한다:

| 에이전트 | OUTPUT_PATH (실제값 대입) |
|----------|---------------------------|
| `tss-static-analyzer` | `/var/folders/.../tss.a1b2c3d4/step2-static.json` |
| `tss-binary-analyzer` | `/var/folders/.../tss.a1b2c3d4/step3-binary.json` |
| `tss-skill-analyzer` | `/var/folders/.../tss.a1b2c3d4/step4-skill.json` |
| `tss-sensitive-patterns` | `/var/folders/.../tss.a1b2c3d4/step5-sensitive.json` |
| `tss-policy-verifier` | `/var/folders/.../tss.a1b2c3d4/step6-policy.json` |
| `tss-prompt-optimizer` | `/var/folders/.../tss.a1b2c3d4/step7-prompt.json` |
| `tss-sbom` | `/var/folders/.../tss.a1b2c3d4/step8-sbom.json` |

#### 체크포인트 (배치 복귀 후 — Bash, 파일=진실 검증)

```bash
D="/var/folders/.../tss.a1b2c3d4"   # 실제 SCAN_TMP 값 대입
python3 - "$D" <<'PY'
import json, sys, os
d = sys.argv[1]
expect = {
 "step1-repo-indexer":"repo-indexer","step2-static":"static","step3-binary":"binary",
 "step4-skill":"skill","step5-sensitive":"sensitive","step6-policy":"policy",
 "step7-prompt":"prompt","step8-sbom":"sbom",
}
missing=[]
for stem in expect:
    p=os.path.join(d,stem+".json")
    if not os.path.exists(p): print(f"{stem}: MISSING"); missing.append(stem); continue
    try:
        obj=json.load(open(p)); m=obj.get("_meta",{})
        print(f"{stem}: OK  findings={m.get('findings','?')} scanned={m.get('files_scanned','?')}")
    except Exception as e:
        print(f"{stem}: INVALID ({e})"); missing.append(stem)
print("MISSING_OR_INVALID="+(",".join(missing) if missing else "NONE"))
PY
```

#### 재시도·중단 정책 (D=실패 시 중단)

- `MISSING_OR_INVALID`에 나온 에이전트만 **타깃 재호출(1회)** → 체크포인트 재실행.
- 1회 재시도 후에도 남으면 → **어떤 에이전트가 왜 실패했는지 명시하고 스캔을 중단**한다.
  부분 진행하지 않는다(보안 스캔 완전성 우선 — 사용자 확정).
- `MISSING_OR_INVALID=NONE`(전 8개 OK)일 때만 Phase 2로 라우팅한다.

### Phase 2 — 순차 분석 (단계 4.5 → 4.6 → 8.5, Phase 1 완료 후)

각 에이전트 프롬프트에 `SCAN_TMP` 경로 + 입력 파일 목록 + `OUTPUT_PATH`를 전달한다.
각 호출 복귀 후 **OUTPUT_PATH 존재를 Bash로 확인**한 뒤 다음으로 진행한다(파일=진실).

1. `tss-relationship-graph` ← SCAN_TMP 실제값 + step1–8 파일 경로 목록
   → OUTPUT_PATH: `/var/folders/.../tss.a1b2c3d4/step4.5-graph.json`
2. `tss-model-validity` ← 동일
   → OUTPUT_PATH: `/var/folders/.../tss.a1b2c3d4/step4.6-model.json`
3. `tss-deepdive` ← SCAN_TMP 실제값 + step1–8 파일 경로 목록
   → OUTPUT_PATH: `/var/folders/.../tss.a1b2c3d4/step8.5-deepdive.json`

### Phase 3 — 보고서 생성 (단계 9 → 10, Phase 2 완료 후)

각 호출 복귀 후 OUTPUT_PATH 파일 존재를 `test -f`로 확인한 뒤 진행한다(파일=진실. sleep 폴링·백그라운드 대기 금지).

**크기 게이트**: 단계 9 산출 후 아래를 측정해 모드를 결정한다.

```bash
FILE_SIZE=$(wc -c < "$SCAN_TMP/step9-english.json" | tr -d ' ')
FINDING_COUNT=$(python3 -c "
import json,sys
d=json.load(open('$SCAN_TMP/step9-english.json'))
er=d.get('english_report',d)
arrs=['static_code_findings','binary_analysis_findings','skill_risk_findings',
      'agent_policy_findings','sensitive_patterns','prompt_optimization',
      'relationship_findings','model_validity_findings']
print(sum(len(er.get(k,[])) for k in arrs))
")
# 게이트: 40KB 또는 40 findings 초과 시 분할 모드
if [ "$FILE_SIZE" -ge 40960 ] || [ "$FINDING_COUNT" -ge 40 ]; then
  MODE=split
else
  MODE=single
fi
echo "Phase 3 mode: $MODE (size=${FILE_SIZE}B, findings=$FINDING_COUNT)"
```

#### 3-A. 단계 9 — 영문 보고서 병합 (tss-report-merger)

`tss-report-merger` 프롬프트:
- SCAN_TMP 실제값 + 모든 step*.json 경로 목록
- OUTPUT_PATH: `$SCAN_TMP/step9-english.json`

복귀 후 즉시 `test -f "$SCAN_TMP/step9-english.json"` 확인.

#### 3-B. 단계 10 — 번역 (크기 게이트에 따라 분기)

**단일 모드 (MODE=single)**:
`tss-translator` 프롬프트:
- INPUT_PATH: `$SCAN_TMP/step9-english.json`
- OUTPUT_PATH: `$OUT_DIR/scanreport-$TIMESTAMP.json`
  (OUT_DIR 실제값 + `/scanreport-` + TIMESTAMP 실제값 + `.json`)

**분할 모드 (MODE=split)**: 카테고리 5묶음을 병렬 `tss-translator`로 처리하되,
**대형 배열 카테고리는 미리 조각내어 hang을 원천 예방**한다(v2.4.1-auto).

**(1) 카테고리 단위 분할 우선(권장 기본값) — v2.4.1-auto 실측 반영.**
번역기 ANTI-HANG CONTRACT 적용 후에는 **단일 카테고리 조각이 30–120초에 안정적으로 완료**된다
(실측). 따라서 기본 전략은 **"카테고리(또는 소수 카테고리 묶음)당 조각 1개"**이며, 큰 배열이라도
그 카테고리를 통째로 한 조각에 담는다(예: static 10개, recommendations 11개 각각 단독 조각).
- **`ITEM_RANGE` 슬라이스는 기본값이 아니라 최후 백스톱**이다. 실측상 워커가 end-exclusive 범위를
  일관되게 지키지 못해 **경계 항목이 중복**되는 파싱-후 parity 불일치가 발생했다(static KR=11/EN=10 등).
  그러므로 슬라이싱은 "단일 카테고리 조각조차 반복해서 hang/과대해 실패"할 때만 쓰고, 이때
  프롬프트에 **정확한 id 목록**(예: "REC-001..REC-006만")을 명시해 중복을 원천 차단한다.
- 조각 파일명: 기본 `step10-frag-N.json`. 부득이 슬라이스 시 `-Na.json`/`-Nb.json`(정렬·연속).
  조립기가 동일 키 배열을 정렬 순서대로 concat한다.

기본 5묶음(각 배열이 CHUNK 이하일 때):
| Fragment | CATEGORIES |
|----------|-----------|
| 1 | `repository_summary` |
| 2 | `static_code_findings,binary_analysis_findings` |
| 3 | `skill_risk_findings,agent_policy_findings` |
| 4 | `sensitive_patterns,prompt_optimization,sbom_analysis` |
| 5 | `relationship_findings,model_validity_findings,recommendations` |

각 translator 프롬프트: `INPUT_PATH`, `CATEGORIES`, (해당 시)`ITEM_RANGE`, `OUTPUT_PATH`, 모드 "Fragment call — Mode B".

**(2) 완료 대기 = 파일 출현.** async 실행 시 각 조각의 OUTPUT_PATH가 나타날 때까지 대기한다
(`until [ -f <path> ]; do sleep 5; done` 형태의 파일-appear 대기 허용).

**(3) 스톨 자동 복구 (무진전 감지 → 재분할, 사용자 확인 없이).**
어떤 조각이 발주 후 **진전 없이 정체**(예: `progress.log` 무성장 + 파일 미생성 상태가 지속)되면
사용자에게 묻지 말고 다음을 자동 수행한다:
  1. 해당 translator를 `TaskStop`으로 중단.
  2. 그 조각이 **다중 카테고리**였다면 → 카테고리별 **단일 조각**으로 쪼개 재발주.
  3. 이미 **단일 배열 카테고리**였다면 → `ITEM_RANGE`를 **절반**으로 더 쪼개 재발주(≤ 4항목까지 축소 가능).
  4. 재발주 조각들의 파일 출현을 다시 대기.
관찰된 근본 원인은 번역기의 영문 재출력·단일 거대 Write였고, 이는 translator 프롬프트의
ANTI-HANG CONTRACT로 1차 예방된다. 위 재분할은 그래도 남는 경우의 백스톱이다.

#### 3-C. 단계 10.5 — 조립 (분할 모드 한정, 결정론·셸 허용 예외)

모든 조각의 파일 출현을 확인한 뒤, **조립 전에 각 조각이 유효 JSON인지 먼저 검증**한다(v2.4.1-auto).
번역기가 이스케이프 안 된 큰따옴표 등으로 깨진 JSON을 쓰면 조립기가 통째로 실패하므로, 깨진 조각은
사용자 확인 없이 **해당 카테고리만 재번역(JSON-safety 지시 명시)** 후 재검증한다:

```bash
D="/var/folders/.../tss.a1b2c3d4"
for f in "$D"/step10-frag-*.json; do
  python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$f" 2>/dev/null \
    || echo "INVALID_JSON: $f  → 해당 카테고리 재번역 필요"
done
```

그 다음 **디렉터리의 모든 `step10-frag-*.json`을 동적으로** 조립한다
(고정 5개 가정 금지 — 재분할로 `-2a/-2b` 등이 생겼을 수 있음).

**⚠️ 셸 호환(zsh):** `--frags $(ls ...)` 처럼 명령치환 결과를 unquoted로 넘기면 **zsh는 단어분할을
하지 않아** 여러 파일이 하나의 인자로 뭉쳐 `Fragment file not found`로 실패한다. 그러므로
`--frags`를 **직접 나열하지 말고**, 조립기의 자동수집을 쓴다: `SCAN_TMP` env만 실제값으로 설정하고
`--frags`를 생략하면 스크립트가 `$SCAN_TMP/step10-frag-*.json`을 **정렬 자동수집**해 동일 키 배열을
순서대로 concat한다(셸 무관, 결정론적).

```bash
SCAN_TMP="/var/folders/.../tss.a1b2c3d4" \
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/assemble_bilingual.py" \
  --english "/var/folders/.../tss.a1b2c3d4/step9-english.json" \
  --out "/Users/user/my-project/scanreport-20260623150000.json"
```

(env `CLAUDE_PLUGIN_ROOT` 미설정 시 `scripts/assemble_bilingual.py` 상대경로로 폴백.
조각을 명시해야 할 불가피한 경우에만 `--frags a.json b.json …`을 **공백으로 직접 나열**한다 — 명령치환 금지.)

최종 산출 검증 — EN/KR 항목 수 일치까지 확인:
```bash
test -f "$OUT_DIR/scanreport-$TIMESTAMP.json" \
  && echo "REPORT OK" || echo "FAIL: bilingual report not written"
python3 - "$OUT_DIR/scanreport-$TIMESTAMP.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
er,kr=d.get("english_report",{}),d.get("korean_report",{})
arrs=['static_code_findings','binary_analysis_findings','skill_risk_findings',
      'agent_policy_findings','sensitive_patterns','prompt_optimization',
      'relationship_findings','model_validity_findings','recommendations']
bad=[k for k in arrs if len(er.get(k,[]))!=len(kr.get(k,[]))]
print("PARITY_OK" if not bad else "PARITY_MISMATCH="+",".join(bad))
PY
```
`PARITY_MISMATCH`이 나오면 해당 카테고리만 translator로 재발주 후 재조립한다(자동, 사용자 확인 없이).

### Phase 4 — HTML 리포트 (단계 11, Phase 3 완료 후)

**(a) compliance_tags 검증 (HTML 생성 직전 — 단계 11 계열 셸 허용):**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_compliance_tags.py" \
  "/Users/user/my-project/scanreport-20260623150000.json"
# (env 미설정 시 repo scripts/validate_compliance_tags.py로 폴백)
# exit 1(오류) → 오류 카테고리를 보고하고 HTML 생성 없이 중단.
# exit 2(경고만) → 경고 요약 후 진행. exit 0 → 정상 진행.
```

**(b) HTML 생성:** `tss-html-report` ← `/Users/user/my-project/scanreport-20260623150000.json` 경로 전달
(OUT_DIR 실제값 + `/scanreport-` + TIMESTAMP 실제값 + `.json`)

### Phase 5 — 결과 보고

산출 파일 경로(JSON·HTML), `_meta` 집계 요약, 그래프 verdict, 주요 Critical/High finding 상위 3건을 보고한다.
배치 진행 로그(`progress.log`)가 있으면 함께 요약한다. 완료 후 임시 디렉터리를 정리한다:

```bash
rm -rf "/var/folders/.../tss.a1b2c3d4"   # 실제 SCAN_TMP 값 대입
```

---

## 실행 절차 — Claude Desktop

Claude Desktop에서는 아래 **스캔 순서** 표에 따라 각 `@sub-skill` 을 순서대로 호출한다.
모든 finding 산출 후 단계 9(병합) → 10(번역) → 11(HTML) 순으로 완주한다.

### AI 에이전트 구성요소 스캔 범위 확인 (단계 1 인덱싱 직후, 1회)

대상 폴더에 AI 에이전트/도구 구성요소(예: `.claude/`, `.cursor/`, `AGENTS.md`, `SKILL.md`,
`.mcp.json`, `agents/`, `prompts/`, `copilot-instructions.md`)가 있는지 인덱싱 결과에서 확인한다.
이 항목들은 애플리케이션 소스가 아니라 AI 도구 설정·프롬프트·권한 구성일 수 있어, 스캔 포함
여부는 사용자가 결정할 사안이다.

- **발견되지 않으면** 아무 질문 없이 그대로 진행한다.
- **하나 이상 발견되면**, 나머지 분석을 시작하기 전에 사용자에게 대화로 **정확히 1회** 묻는다:
  "대상에서 AI 에이전트 관련 구성요소(`<발견 목록>`)가 발견되었습니다. 스캔 범위에 포함할까요?
  (포함 권장 / 제외)". 답을 받은 뒤에는 다시 묻지 않고 완주한다.
- **제외**를 선택하면 해당 경로의 내용을 분석하지 않고(존재만 인지), 최종 리포트
  `repository_summary.ai_agent_scope`에 `"excluded"`를, **포함** 시 `"included"`를 기록한다.

> Desktop은 샌드박스라 자동 권한 셋업(Code의 Phase 0'')이 필요 없다 — 파일 생성·셸 실행을
> 하지 않으므로 권한 게이트 자체가 없다.

### Compliance Tagging (Schema V1.4)

단계 1–8이 각 finding에 `compliance_tags`(KISA·AILLM·TA)를 부여하고(CTID-D 규칙,
`references/docs/compliance-tagmap-distilled.md`), 단계 8.5가 검증·교정한다(CTID-V,
`references/docs/compliance-tagging-deepdive.md`). 단계 9–11은 태그 읽기전용 —
번역(단계 10)은 태그를 EN/KO 동일하게 유지하고, HTML(단계 11)은 배지로 렌더한다.

---

## 참조 (방법론 상세)

## 스캔 순서

| 단계 | 스킬 | 설명 |
|------|------|------|
| 0 | `@source-handler` | 소스 준비 (ZIP 해제, GitHub 클론) — 셸 사용 허용 단계 |
| 1 | `@repo-indexer` | 리포지토리 인덱싱 |
| 2 | `@static-code-analyzer` | 정적 코드 분석 |
| 3 | `@binary-analyzer` | 바이너리 분석 |
| 4 | `@skill-security-analyzer` | Skill/도구 보안 분석 |
| **4.5** | **`@relationship-graph-analyzer`** | **컴포넌트 연관관계 그래프 + 위험 전파 (v2.1.0+)** |
| **4.6** | **`@model-validity-analyzer`** | **모델 유효성/진부화 판정 (v2.1.0+)** |
| 5 | `@sensitive-pattern-matcher` | 민감 패턴 매칭 |
| 6 | `@agent-policy-verifier` | 에이전트 정책 검증 |
| 7 | `@prompt-optimizer` | 프롬프트/포맷 최적화 |
| 8 | `@sbom-analyzer` | SBOM 및 의존성 분석 |
| **8.5** | **`@securityreports-deepdive`** | **심층 분석(트리아지) — Medium↑ finding에 status/deep_dive_result/code_fix 채움 (v2.1.1+)** |
| 9 | `@report-merger` | 영문 보고서 병합 |
| 10 | `@bilingual-translator` | 한글 번역 및 최종 보고서 생성 |
| **11** | **`@html-report-generator`** | **HTML 리포트 출력 — 번들 스크립트로 JSON→정적 HTML 생성 (v2.2.0+)** |

**단계 4.5–4.6은 단계 4 완료 후 순차 실행. 셸/코드 실행 없이 Claude 추론으로만 수행.**
**단계 8.5는 단계 1–8의 모든 finding 산출 후, 병합(9) 이전에 수행. 셸/코드 실행 없이 Claude 추론으로만.**
**Compliance Tagging (v2.5.0/Schema V1.4): 단계 1–8이 CTID-D로 `compliance_tags` 부여, 단계 8.5가 CTID-V로 검증·교정(태그 수정 가능한 유일 단계), 단계 9–11은 태그 읽기전용. 단계 11 직전 `validate_compliance_tags.py`로 검증.**
**단계 10.5(조립)는 분할 모드 한정 결정론·셸 허용 예외 — `assemble_bilingual.py` 실행만. LLM 추론 없음. 단계 0·11과 동일 성격.**
**단계 11은 단계 10의 bilingual JSON 산출 후 수행. 스크립트 실행이 허용되는 예외 단계(단계 0과 동일 성격)이며, LLM 추론 없이 결정론적 파일 처리만 수행한다. 별도 요구가 없으면 JSON과 KO HTML 리포트를 함께 출력한다.**
**`references/sub-skills/relationship-graph-analyzer.md`, `references/sub-skills/model-validity-analyzer.md`, `references/sub-skills/securityreports-deepdive.md`, `references/sub-skills/html-report-generator.md` 참조.**

## 분석 전략

### Phase 1 — Broad Scan (Level 1)
- 전체 리포지토리를 스캔하여 후보 위험 식별
- 각 스킬이 독립적으로 Level 1 분석 수행

### Phase 2 — Deep Dive (Level 2-3, MAX DEPTH = 3)
**실행 주체: 단계 8.5 `@securityreports-deepdive`** (`references/sub-skills/securityreports-deepdive.md`).
단계 1–8의 모든 finding 산출 후, 병합(9) 전에 반드시 수행한다. 개념 서술에 그치지 말고 실제로 호출하여 대상 finding에 `status`/`deep_dive_result`/`code_fix`를 채운다.

Deep Dive 수행 기준:
- Severity가 Medium 또는 High인 경우
- 동작이 불명확한 경우("could/may/potentially")
- 민감 정보가 관련된 경우

조치할 수정 코드는 **`code_fix` 구조화 필드**로 격리한다(JSON 안전 규칙: 코드는 문자열 값·이스케이프, 코드펜스 금지). 상세는 deepdive 서브스킬·`SCHEMA_V1.3_ENFORCEMENT.md` §2.7.

### 최종 판정 분류
- `Confirmed` - 확인된 위험
- `Mitigated` - 완화된 위험
- `False Positive` - 오탐 (근거 포함)

## 출력 형식

### ⚠️ 필수: Schema V1.3 엄격 준수

**임의로 필드를 추가/변경/제거하면 뷰어 호환성이 깨집니다.**
**참조**: `references/docs/SCHEMA_V1.3_ENFORCEMENT.md`, `references/docs/claude-threat-scan-json-schema-v1.3.md`

### 파일명 규칙
```
scanreport-YYYYMMDDhhmmss.json
```

### JSON 구조 (V1.3 — v1.2 완전 호환)
```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",
  "scan_metadata": {
    "scan_date": "ISO 8601 format",
    "scanner_version": "Claude Threat Scan V2.5",
    "repository": "repo-name",
    "target_repository": "repo-name",
    "total_files_scanned": 0,
    "total_files": 0,
    "code_files": 0,
    "analysis_depth": 3,
    "scan_depth": 3
  },
  "english_report": {
    "repository_summary": {
      "graph_verdict": {}
    },
    "static_code_findings": [],
    "binary_analysis_findings": [],
    "skill_risk_findings": [],
    "agent_policy_findings": [],
    "sensitive_patterns": [],
    "prompt_optimization": [],
    "sbom_analysis": {},
    "relationship_findings": [],
    "model_validity_findings": [],
    "recommendations": []
  },
  "korean_report": {
    "repository_summary": {
      "graph_verdict": {}
    },
    "static_code_findings": [],
    "binary_analysis_findings": [],
    "skill_risk_findings": [],
    "agent_policy_findings": [],
    "sensitive_patterns": [],
    "prompt_optimization": [],
    "sbom_analysis": {},
    "relationship_findings": [],
    "model_validity_findings": [],
    "recommendations": []
  }
}
```

**V1.3 신규 optional 필드 (단계 4.5–4.6 산출물)**:
- `repository_summary.graph_verdict` — 그래프 전파 후 worst component 기준 summary verdict
- `relationship_findings[]` — REL-NNN, 컴포넌트 연관관계 그래프 분석
- `model_validity_findings[]` — MODEL-NNN, 모델 유효성/진부화 판정
- 각 finding의 `verdict` (`INSTALL_OK`/`REVIEW`/`DISABLE`/`REMOVE`)
- 각 finding의 `model_effectiveness` (`VALID`/`DEGRADED`/`OBSOLETE`/`MODEL_LOCKED`)

### ❌ 금지 필드 (절대 추가하지 마세요)
- `findings_summary` - 스키마에 없음
- `executive_summary` - 스키마에 없음  
- `findings` (단일 배열) - 카테고리별 배열 사용
- `positive_findings` - 스키마에 없음
- `scan_id`, `scan_type`, `target`, `timestamp`, `target_info` - 스키마 외 필드
- `title`, `category`, `cwe`, `owasp` (finding 내) - `issue` 사용
- `remediation` - `recommendation` 사용
- `code_snippet` - 스키마에 없음
- severity 소문자 - 대문자 시작 필수
- verdict 소문자 - 대문자 필수 (`REMOVE` not `remove`)

## 제약 사항

- **단계 0(`@source-handler`)·단계 11(`@html-report-generator`)만 스크립트/파일 생성 허용** — 단계 0은 소스 준비(git clone/unzip), 단계 11은 결정론적 HTML 리포트 생성에 한정
- 단계 1–10: 셸/코드 실행 금지, Claude 추론으로만 분석 수행 (Claude Desktop 샌드박스 호환).
  단, Claude Code 플러그인 에이전트는 **읽기 전용 파일 탐색 도구 `Glob`/`Grep` 사용 허용**
  (셸/코드 실행이 아님) — 전체 트리 완전 열거·커버리지 확보용. (v2.4.1-auto)
- 단계 1–10은 파일 생성 금지 (JSON 출력만 수행). 단계 11은 번들 스크립트로 HTML 파일 생성 — 입력 JSON을 변형하지 않고 그대로 임베드
- 각 스킬의 결과를 신뢰하되 일관성 검증 수행

## 사용 예시

```
사용자: @threat-scan-orchestrator /Users/user/project 전체 보안 스캔 수행

응답: 
1. 리포지토리 인덱싱 중...
2. 정적 코드 분석 중...
...
9. 보고서 생성 완료

[JSON 보고서 출력]
```
