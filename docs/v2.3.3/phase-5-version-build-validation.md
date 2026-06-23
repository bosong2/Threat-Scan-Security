# Phase 5 — 버전 범프 · 빌드 · E2E 검증 · 릴리스

## 목표

v2.3.3 변경을 버전 동기화하고, Dual-Mode 빌드·E2E 스캔으로 회귀와 보안 목표 달성을
검증한다.

## Part A — 버전 동기화

| 파일 | 변경 |
|------|------|
| `VERSION` | `2.3.2` → `2.3.3` |
| `.claude-plugin/plugin.json` | `version` → `2.3.3`, `hooks` 키 추가(Phase 3) |
| `CHANGELOG.md` | `[2.3.3]` 항목 추가 |

### CHANGELOG 초안

```markdown
## [2.3.3] — 2026-06-2X

### Security
- **Secret 반환 계약 강제** — 탐지 워커(tss-sensitive-patterns/static-analyzer)가
  raw secret/PII 값을 절대 반환하지 않고 `masked_value`만 산출하도록 공유 방법론에
  MASKING CONTRACT 명문화. 콘솔·JSON 누출 차단(1차 방어선).
- **SubagentStop 리댁션 훅** — 알려진 secret 패턴(AWS/GitHub/PrivateKey/PII)을
  결정론적 정규식으로 마스킹하는 hooks/hooks.json + scripts/redact_secrets.sh 신설
  (2차 방어선, LLM 호출 없음).

### Changed
- **오케스트레이터를 얇은 컨텍스트 master로 재설계** — 워커 산출물을 $SCAN_TMP 파일로
  라우팅, 마스터 컨텍스트에 finding 본문 누적 제거. Phase 경계 Bash 무결성 체크포인트
  추가. 이로써 마스터 Opus 사용을 토큰상 정당화(SecurityScanCode securityscan-triage
  패턴 이식). allowed-tools에 Write 추가.
- **모델·권한 차등 정합화** — 탐지·분석 워커 tools:Read(셸·쓰기 차단), 셸 허용 3개로
  한정. tss-deepdive를 sonnet→opus 상향.

### Added
- 워커 자기보고 `_meta` footer(files_scanned/findings/depthReached) + 마스터 집계.
- scripts/agent_efficiency.sh — 사후 트랜스크립트 기반 per-agent 효율 요약(best-effort).
```

## Part B — Dual-Mode 빌드

```bash
cd Threat-scan-security
bash build_claude_desktop.sh
```

- Code 플러그인: `.claude-plugin/` + `agents/` + `commands/` + `hooks/` + `scripts/`.
- Desktop dist: `dist_claude_desktop/` — 마스킹 계약 반영, 훅·redact 스크립트 **제외**.

## Part C — E2E 검증 시나리오

### C-1. 보안 목표 (핵심)

테스트 픽스처(의도적으로 AWS 키·GitHub 토큰을 심은 소형 리포)로 `/threat-scan` 실행:

- [ ] 콘솔 출력·`scanreport-*.json`·HTML 어디에도 **raw secret 미노출**
      (`AKIAIOSFODNN7EXAMPLE` 류 원문 grep → 0건).
- [ ] finding에 `masked_value`(`AKIA****`)와 locator(file/line)는 정상 존재.
- [ ] secret이 정상 탐지됨(마스킹이 탐지 누락으로 이어지지 않음).

### C-2. 오케스트레이션 완주 (v2.3.2 회귀 방지)

- [ ] Phase 0→1→2→3→4→5 완주, JSON + KO HTML 산출.
- [ ] 마스터 컨텍스트가 얇게 유지됨(중간 finding 본문 누적 없음 — 토큰 추이로 확인).
- [ ] Phase 경계 체크포인트가 누락 워커를 1회 재호출하는지(누락 주입 테스트).

### C-3. 권한·모델

- [ ] 탐지 워커가 셸 호출 시도 시 권한 거부(tools:Read 강제 확인).
- [ ] 각 워커가 frontmatter 모델대로 실행(트랜스크립트 확인).

### C-4. 효율 모니터링

- [ ] `_meta` 집계 요약이 Phase 5 보고에 포함.
- [ ] `scripts/agent_efficiency.sh`가 트랜스크립트에서 per-agent 요약 산출(또는 graceful skip).

### C-5. Dual-Mode 무결성

- [ ] Desktop dist에 `tss-*` 이름이 Code Plugin 섹션 안에만(BUG-02 회귀 없음).
- [ ] Desktop dist에 마스킹 계약 반영, `redact_secrets.sh` 미포함.

## Part D — 릴리스

```bash
# 버전 검증
grep -c "2.3.3" VERSION .claude-plugin/plugin.json
# 커밋·태그 (사용자 승인 후)
git add -A && git commit -m "release: v2.3.3 — master orchestration redesign + secret redaction"
git tag v2.3.3
```

> 커밋·푸시·태그는 **사용자 명시 승인 후** 수행한다.

## 완료 조건 (검증 가능)

- [ ] `VERSION`/`plugin.json` = 2.3.3, CHANGELOG `[2.3.3]` 존재.
- [ ] C-1 보안 목표 전부 통과(raw secret 0건, masked_value 정상).
- [ ] C-2 오케스트레이션 완주, 회귀 없음.
- [ ] C-3~C-5 통과.
- [ ] Desktop 빌드 성공, Dual-Mode 무결성 유지.

## 전체 검증 스크립트

```bash
cd Threat-scan-security
# 버전
grep -q "2.3.3" VERSION && grep -q '"2.3.3"' .claude-plugin/plugin.json && echo "version OK"
# 보안 (픽스처 스캔 후)
RAW="AKIAIOSFODNN7EXAMPLE"
grep -rc "$RAW" scanreport-*.json *.html 2>/dev/null | grep -v ":0" && echo "FAIL: raw secret leaked" || echo "OK: no raw secret"
grep -c "masked_value" scanreport-*.json   # ≥ 1
# 빌드
bash build_claude_desktop.sh >/dev/null && echo "desktop build OK"
test ! -f dist_claude_desktop/threat-scan-security/scripts/redact_secrets.sh && echo "OK: hook excluded from desktop"
```
