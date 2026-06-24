#!/usr/bin/env bash
# log_completion.sh — SubagentStop hook (완료 로깅, v2.4.0)
# 각 tss-* 서브에이전트 종료 시 발화한다. stdin: hook payload JSON.
# 에이전트 종료 사실을 시간과 함께 기록한다 — 배치 진행 가시성(계층 ③).
# LLM 호출 없음. 페이로드를 변경하지 않고 그대로 통과시킨다(non-blocking 로깅).
set -euo pipefail

PAYLOAD="$(cat)"

# 에이전트 이름 추출 (jq 없으면 grep 폴백)
NAME=""
if command -v jq &>/dev/null; then
  NAME=$(printf '%s' "$PAYLOAD" | jq -r '.agentName // .agent // .subagent_type // empty' 2>/dev/null || true)
fi
[ -z "$NAME" ] && NAME=$(printf '%s' "$PAYLOAD" | grep -oE 'tss-[a-z-]+' | head -1 || true)
[ -z "$NAME" ] && NAME="tss-unknown"

# SCAN_TMP 추정: 페이로드에서 tss.<id> 임시 경로를 찾는다. 없으면 시스템 임시 디렉터리.
DIR=$(printf '%s' "$PAYLOAD" | grep -oE '/[^"]*/tss\.[A-Za-z0-9]+' | head -1 || true)
if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
  DIR="${TMPDIR:-/tmp}"
fi

TS=$(date '+%Y-%m-%d %H:%M:%S')
printf '%s  %s stopped\n' "$TS" "$NAME" >> "$DIR/progress.log" 2>/dev/null || true

# 페이로드 원본 그대로 통과 (체이닝·non-blocking)
printf '%s' "$PAYLOAD"
