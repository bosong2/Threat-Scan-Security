#!/usr/bin/env bash
# redact_secrets.sh — SubagentStop hook (2차 방어선, v2.3.3)
# stdin: hook payload JSON. 워커 반환 텍스트에서 raw secret을 결정론적으로 마스킹한다.
# LLM 호출 없음 — 순수 정규식 sed 파이프라인.
set -euo pipefail

PAYLOAD="$(cat)"

# jq가 없으면 원본 그대로 통과 (graceful degradation)
if ! command -v jq &>/dev/null; then
  printf '%s' "$PAYLOAD"
  exit 0
fi

# 워커 최종 메시지(assistant content) 추출 → 마스킹 → 재조립
CONTENT=$(printf '%s' "$PAYLOAD" | jq -r '.message.content // empty' 2>/dev/null || true)

if [ -z "$CONTENT" ]; then
  # 구조가 예상과 다르면 원본 통과
  printf '%s' "$PAYLOAD"
  exit 0
fi

MASKED=$(printf '%s' "$CONTENT" | sed \
  -e 's/AKIA[0-9A-Z]\{16\}/AKIA****************/g' \
  -e 's/ghp_[A-Za-z0-9]\{36,\}/ghp_****/g' \
  -e 's/gho_[A-Za-z0-9]\{36,\}/gho_****/g' \
  -e 's/github_pat_[A-Za-z0-9_]\{1,\}/github_pat_****/g' \
  -e 's/glpat-[A-Za-z0-9-]\{20,\}/glpat-****/g' \
  -e 's/xox[baprs]-[A-Za-z0-9-]\{1,\}/xox*-****/g' \
  -e 's/sk_live_[A-Za-z0-9]\{24,\}/sk_live_****/g' \
  -e 's/AIza[A-Za-z0-9_-]\{35\}/AIza****/g' \
  -e 's/sk-[A-Za-z0-9]\{48\}/sk-****/g' \
  -e 's/-----BEGIN [A-Z ]*PRIVATE KEY-----[^-]*-----END [A-Z ]*PRIVATE KEY-----/[REDACTED PRIVATE KEY]/g' \
)

# 마스킹된 content를 payload에 재조립
printf '%s' "$PAYLOAD" | jq --arg c "$MASKED" '.message.content = $c'
