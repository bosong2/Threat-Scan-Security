---
description: Pre-register permission allow-rules so /threat-scan runs without prompts (optional — auto-run on first scan)
---

프로젝트 `.claude/settings.local.json`에 Claude Threat Scan 파이프라인이 필요로 하는
권한 allow 규칙을 등록한다. 이 커맨드는 **선택사항**이다 — `/threat-scan`을 처음 실행하면
오케스트레이터(Phase 0'')가 규칙 부재를 감지해 **자동으로** 동일 작업을 1회 승인으로 수행한다.
사전 등록을 원하거나 CI 준비용으로 미리 돌리고 싶을 때 사용한다.

## 동작

1. 프로젝트 `.claude/settings.local.json`을 Read한다(없으면 `{"permissions":{"allow":[]}}` 구조로 신규 생성).
2. `permissions.allow` 배열에 아래 규칙을 **병합**한다 — 기존 항목은 보존하고, 중복은 추가하지 않으며,
   절대 덮어쓰지 않는다.
3. Write로 저장한다(권한 프롬프트가 1회 뜨면 승인).
4. 결과를 보고한다: 새로 추가된 규칙 / 이미 있던 규칙 / 최종 파일 경로.

## 등록 규칙 (오케스트레이터 Phase 0''와 동일한 정본 목록)

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

이 목록은 `skills/threat-scan-orchestrator/SKILL.md` Phase 0''의 규칙과 일치해야 한다
(둘 중 하나만 바꾸면 드리프트 발생 — 함께 수정할 것).

> `.claude/settings.local.json`은 `.gitignore` 대상(`.claude/`)이라 커밋되지 않는 로컬 설정이다 — 의도된 동작.
> 완료 후 `/threat-scan <대상>`은 권한 프롬프트 없이 완주한다.
