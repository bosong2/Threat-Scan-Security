# Phase 2 — 마스터 파일 라우팅 + 얇은 컨텍스트 + Opus

## 목표

오케스트레이터를 **얇은 컨텍스트의 master agent**로 재설계한다. 워커 산출물을
`$SCAN_TMP` 파일로 라우팅하여 마스터 컨텍스트에 finding 본문을 누적하지 않게 하고,
이로써 마스터에 **Opus** 모델을 토큰상 정당화한다.

## 근본 원인

현재 `skills/threat-scan-orchestrator/SKILL.md`(Claude Code Plugin 절차):
- 워커 8개+가 반환한 finding JSON 조각을 **마스터 컨텍스트에 그대로 수신**.
- 다음 단계(merger/translator)에 그 조각들을 **컨텍스트로 다시 전달**.
- 결과: 컨텍스트 비대 → Opus 두면 비쌈, 호출 사이 능동 통제 없음.
- `allowed-tools`에 `Write` 없음 → 파일 라우팅 자체가 불가.

## 설계: SecurityScanCode `securityscan-triage` 패턴 이식

```
마스터(얇음) = 제어 흐름 + 파일 경로 + 카운트 + verdict 집계만 보유
워커 산출물  = $SCAN_TMP/<step>-<agent>.json 파일로 라우팅
다음 단계    = 파일 경로를 인자로 받아 파일에서 읽음 (컨텍스트 경유 X)
```

> **주의:** 서브에이전트는 자기 결과를 파일로 직접 쓸 수 없는 환경이 있으므로
> (SecurityScanCode R18 계약), 워커는 JSON 텍스트를 **반환**하고 **마스터가
> `Write` 도구로 파일에 기록**한다. 마스터 컨텍스트에는 잠깐 스쳐가지만, 즉시 파일로
> 내보내고 다음 단계엔 **경로만** 넘기므로 누적되지 않는다.

## 수정

### 1. `allowed-tools`에 `Write` 추가

```yaml
allowed-tools: Agent(tss-source-handler), ... Agent(tss-html-report), Bash, Read, Write
```

### 2. Claude Code Plugin 절차에 `$SCAN_TMP` 라우팅 도입

`## 실행 절차 — Claude Code Plugin` 섹션 상단에 세션 격리 임시 디렉토리 + 출력 경로
고정 블록을 추가(SecurityScanCode Step 0 패턴):

```markdown
### Phase 0' — 세션 격리 + 출력 경로 고정 (Bash, 최초 1회)

OUT_DIR = 호출 폴더(절대경로, cd 이전 고정). 모든 최종 산출물의 집.
SCAN_TMP = mktemp -d (세션 격리). 모든 중간 finding 조각의 집.
TIMESTAMP = date stamp.
→ 이후 모든 Phase가 이 변수를 공유한다.
```

각 Phase의 워커 반환을 **즉시 파일로 내보낸다**:

```markdown
### Phase 1 — 병렬 분석 (ONE message)
8개 에이전트를 동시 호출. 각 반환 JSON을 Write 도구로 즉시 저장:
  $SCAN_TMP/step1-repo-indexer.json
  $SCAN_TMP/step2-static.json
  $SCAN_TMP/step3-binary.json
  ... (8개)
**마스터는 저장 후 finding 본문을 컨텍스트에서 버린다 — 경로와 카운트만 유지.**

### Phase 2 — 순차 분석 (4.5 → 4.6 → 8.5)
relationship-graph/model-validity/deepdive 에이전트에 **앞 단계 파일 경로**를 전달
(finding 본문을 컨텍스트로 재전달하지 않는다). 각 반환도 $SCAN_TMP에 저장.

### Phase 3 — 병합·번역 (9 → 10)
report-merger에 $SCAN_TMP/*.json **경로 목록**을 전달 → english_report 생성.
translator에 그 경로 전달 → bilingual JSON을 $OUT_DIR/scanreport-<TS>.json 으로 저장.

### Phase 4 — HTML (11)
html-report 에이전트에 bilingual JSON 경로 전달.
```

### 3. 호출 사이 Bash 체크포인트 (능동적 master)

각 Phase 경계에서 마스터가 Bash로 무결성을 검증한다 (SecurityScanCode coverage check 패턴):

```markdown
### 체크포인트 (Phase 1 완료 후)
- 기대한 8개 step 파일이 모두 존재하는지 확인. 누락 시 해당 워커 1회 재호출.
- 각 파일이 valid JSON인지 검증 (python -c json.load).
- secret 누출 가드: step2/step5 파일에서 raw secret 패턴 grep → 발견 시 경고.
```

### 4. 마스터 모델 권장: Opus

`SKILL.md` 본문 상단에 운영 노트 추가:

```markdown
> **모델 권장(v2.3.3):** 이 오케스트레이터는 finding 본문을 파일로 라우팅해
> 컨텍스트를 얇게 유지하므로 **Opus** 사용을 권장한다(라우팅·검증 판단력 ↑, 토큰 ↓).
> 워커는 Phase 4 표의 차등 모델을 따른다.
```

> 스킬 자체에는 `model` frontmatter가 적용되지 않으므로(스킬은 메인 세션 모델로 실행),
> 사용자가 세션 모델을 Opus로 두거나 `/threat-scan` 실행 환경에서 선택하도록 안내한다.
> (서브에이전트 모델은 각 `agents/tss-*.md`의 `model` frontmatter로 고정 — Phase 4.)

## Dual-Mode 영향

- **Claude Desktop**: 영향 없음. Desktop은 순차 단일 컨텍스트 실행이라 파일 라우팅·
  `$SCAN_TMP` 개념이 없다. `## 실행 절차 — Claude Desktop` 섹션과 스캔 순서 표는 그대로.
- 변경은 전부 `## 실행 절차 — Claude Code Plugin` 섹션 **안에만** 둔다(BUG-02 회귀 방지).

## 완료 조건 (검증 가능)

- [ ] 오케스트레이터 `allowed-tools`에 `Write` 포함.
- [ ] Code Plugin 절차에 `SCAN_TMP`/`OUT_DIR`/`TIMESTAMP` 고정 블록 존재.
- [ ] 각 Phase가 워커 반환을 `$SCAN_TMP/*.json`으로 저장하고, 다음 단계엔 **경로**를 전달.
- [ ] Phase 경계마다 Bash 무결성 체크포인트(파일 존재·JSON 유효성·secret 가드) 존재.
- [ ] 마스터 Opus 권장 노트 존재.
- [ ] 변경이 모두 `Claude Code Plugin` 섹션 내부 — Desktop 섹션 무변경.

## 검증

```bash
cd Threat-scan-security
grep -n "allowed-tools" skills/threat-scan-orchestrator/SKILL.md | grep -c "Write"   # 1
grep -c "SCAN_TMP" skills/threat-scan-orchestrator/SKILL.md                          # ≥ 1
grep -c "체크포인트" skills/threat-scan-orchestrator/SKILL.md                         # ≥ 1
# Desktop 섹션 오염 없음 (SCAN_TMP는 Code 섹션에만)
awk '/실행 절차 — Claude Desktop/,/^## [^실]/' skills/threat-scan-orchestrator/SKILL.md | grep -c "SCAN_TMP"  # 0
```
