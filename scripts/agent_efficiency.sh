#!/usr/bin/env bash
# agent_efficiency.sh — 사후 트랜스크립트 기반 per-agent 효율 요약 (best-effort, v2.3.3)
# Usage: bash scripts/agent_efficiency.sh [session-id]
# session-id 생략 시 최신 세션 자동 탐지.
set -euo pipefail

PROJECTS_DIR="${HOME}/.claude/projects"

if [ $# -ge 1 ]; then
  SESSION_ID="$1"
  TRANSCRIPT=$(find "$PROJECTS_DIR" -name "*.jsonl" 2>/dev/null \
    | xargs grep -l "$SESSION_ID" 2>/dev/null | head -1 || true)
else
  # 최신 jsonl 파일 자동 탐지
  TRANSCRIPT=$(find "$PROJECTS_DIR" -name "*.jsonl" 2>/dev/null \
    | sort -t_ -k1 | tail -1 || true)
fi

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  echo "⚠ 트랜스크립트를 찾을 수 없습니다 (graceful skip)." >&2
  exit 0
fi

echo "📊 Per-agent 효율 요약 (트랜스크립트: $(basename "$TRANSCRIPT"))"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 - "$TRANSCRIPT" <<'PYEOF'
import json, sys, collections

path = sys.argv[1]
agents = collections.defaultdict(lambda: {"input": 0, "output": 0, "turns": 0})

with open(path) as f:
    for line in f:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        # agent 이름 추출
        name = rec.get("agentName") or rec.get("agent") or ""
        if not name or not name.startswith("tss-"):
            continue
        usage = rec.get("usage") or {}
        agents[name]["input"] += usage.get("input_tokens", 0)
        agents[name]["output"] += usage.get("output_tokens", 0)
        agents[name]["turns"] += 1

if not agents:
    print("(tss-* 에이전트 레코드 없음 — 형식이 다를 수 있음)")
    sys.exit(0)

print(f"{'에이전트':<30} {'input':>8} {'output':>8} {'turns':>6}")
print("-" * 56)
total_in = total_out = 0
for name, s in sorted(agents.items()):
    print(f"{name:<30} {s['input']:>8,} {s['output']:>8,} {s['turns']:>6}")
    total_in += s["input"]
    total_out += s["output"]
print("-" * 56)
print(f"{'TOTAL':<30} {total_in:>8,} {total_out:>8,}")
PYEOF
