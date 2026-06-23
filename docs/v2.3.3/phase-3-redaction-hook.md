# Phase 3 — SubagentStop 리댁션 훅 (2차 방어선)

## 목표

플러그인 `hooks/hooks.json`에 **`SubagentStop` 훅**을 신설하여, 워커 반환물에 raw secret이
남아 있을 경우 **결정론적으로 마스킹**한다. Phase 1(반환 계약)이 1차 방어선, 이 훅이
2차 방어선이다(depth-in-defense).

## 근거 (검증된 제약)

- 오케스트레이터는 실행 중 서브에이전트를 감시할 수 없다 → **호출 종료 시점**의 훅이
  유일한 결정론적 게이트.
- **플러그인** 서브에이전트 frontmatter는 `hooks`를 지원하지 않는다 → 훅은 플러그인
  레벨 `hooks/hooks.json`에 둔다.
- 현재 `hooks/` 디렉토리·`plugin.json` `hooks` 키 **모두 부재** → 신설.

## 설계

### 1. `hooks/hooks.json` 신설

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "tss-sensitive-patterns|tss-static-analyzer",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/scripts/redact_secrets.sh\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

> `matcher`로 secret을 다루는 워커에만 적용해 오버헤드를 최소화한다. SubagentStop 훅은
> 서브에이전트 종료 시점에 그 반환물(트랜스크립트 마지막 메시지)을 stdin으로 받는다.

### 2. `scripts/redact_secrets.sh` 신설 (결정론적 마스킹)

훅 입력(JSON)에서 서브에이전트의 최종 메시지를 읽어, 알려진 secret 패턴을 마스킹한 뒤
반환한다. 마스킹 대상 패턴(결정론적 정규식):

| 패턴 | 정규식(요지) | 마스킹 |
|------|--------------|--------|
| AWS Access Key | `AKIA[0-9A-Z]{16}` | `AKIA****` |
| GitHub Token | `gh[pousr]_[A-Za-z0-9]{36,}` | `ghp_****` |
| Slack Token | `xox[baprs]-[A-Za-z0-9-]+` | `xox*-****` |
| Private Key 블록 | `-----BEGIN ... PRIVATE KEY-----` | `[REDACTED PRIVATE KEY]` |
| 이메일(PII) | `[\w.+-]+@[\w-]+\.[\w.-]+` | `j***@***` |
| 일반 high-entropy 32자+ | base64/hex 연속 | 앞 4자 + `****` |

```bash
#!/usr/bin/env bash
# redact_secrets.sh — SubagentStop 훅. stdin: 훅 페이로드 JSON.
# 워커 반환 텍스트에서 raw secret을 결정론적으로 마스킹한다(2차 방어선).
set -euo pipefail
PAYLOAD="$(cat)"
# 결정론적 sed 파이프라인으로 알려진 패턴 마스킹 후, 훅 출력 규약에 맞게 반환.
# (구현 시 jq로 메시지 추출 → sed 마스킹 → 재조립. LLM 호출 없음.)
printf '%s' "$PAYLOAD" | "${CLAUDE_PLUGIN_ROOT}/scripts/_mask.sed적용"
```

> 실제 구현은 hooks 출력 규약(stdout으로 수정 페이로드 또는 종료코드)에 맞춘다.
> **LLM 추론 없는 순수 정규식**이므로 재현 가능·비용 0.

### 3. `.claude-plugin/plugin.json`에 `hooks` 등록

```json
{
  "name": "threat-scan-security",
  "version": "2.3.3",
  ...
  "hooks": "./hooks/hooks.json"
}
```

### 4. `build_claude_desktop.sh` — Desktop에서 훅 제외

훅은 Claude Code 전용이다. Desktop 빌드는 `hooks/`·`scripts/redact_secrets.sh`를
**복사하지 않도록** 명시(현재 build 스크립트는 `scripts/`를 일부 복사하므로
redact 스크립트가 Desktop dist에 들어가지 않게 예외 처리).

## 한계 명시 (정직한 범위)

- 훅은 **알려진 패턴**만 마스킹한다. 신종/난독화 secret은 Phase 1 반환 계약이 1차로 막아야 한다.
- SubagentStop 훅이 반환물을 수정하는 동작은 hooks 사양에 의존하므로, 사양상 "수정 주입"이
  불가하면 **차선책**으로 전환: 훅이 raw secret 탐지 시 **경고를 stderr로 남기고 통과**시키되,
  최종 보고에 "잠재 누출 N건 — 워커 계약 위반" 으로 표면화(사용자가 인지 가능).
- 이 한계는 Phase 5 검증에서 실제 hooks 동작을 확인해 확정한다.

## 완료 조건 (검증 가능)

- [ ] `hooks/hooks.json` 존재, `SubagentStop` + matcher(secret 워커) 등록.
- [ ] `scripts/redact_secrets.sh` 존재, 실행 권한, LLM 호출 없음(순수 정규식).
- [ ] `.claude-plugin/plugin.json`에 `"hooks": "./hooks/hooks.json"` 등록.
- [ ] 알려진 패턴(AWS/GitHub/PrivateKey 등)에 대한 마스킹 단위 테스트 통과.
- [ ] Desktop 빌드 dist에 `redact_secrets.sh` 미포함.

## 검증

```bash
cd Threat-scan-security
test -f hooks/hooks.json && grep -c "SubagentStop" hooks/hooks.json        # 1
test -x scripts/redact_secrets.sh                                          # 존재·실행권한
grep -c '"hooks"' .claude-plugin/plugin.json                               # 1
# 마스킹 동작 (샘플 입력)
echo 'key=AKIAIOSFODNN7EXAMPLE' | bash scripts/redact_secrets.sh | grep -c "AKIA\*\*\*\*"  # ≥ 1, raw 미노출
echo 'key=AKIAIOSFODNN7EXAMPLE' | bash scripts/redact_secrets.sh | grep -c "IOSFODNN7"      # 0 (raw 제거 확인)
# Desktop dist 비포함
bash build_claude_desktop.sh >/dev/null && \
  test ! -f dist_claude_desktop/threat-scan-security/scripts/redact_secrets.sh && echo "OK: not in desktop dist"
```
