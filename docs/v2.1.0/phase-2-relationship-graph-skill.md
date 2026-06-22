# Phase 2 — 연관관계 그래프 스킬 (Goal Prompt)

> 선행 의존성: **Phase 1**

## 🎯 목표 (Objective)

검사 대상의 컴포넌트(Plugin/Skill/Agent/Hook/MCP/Command) 간 **의존성 그래프**를 구성하고 **위험을 전파**하는 신규 프롬프트 스킬을 만든다. 기존 `skill-security-analyzer`의 "최대 3단계 참조 추적"을 그래프 + 전파로 일반화한다.

## 📥 참조 입력 (Inputs)

- `skills/skill-security-analyzer/SKILL.md` (3단계 추적 — 형식·톤 참고)
- `skills/threat-scan-orchestrator/SKILL.md` (스킬 호출 규약)
- Phase 1 v1.3 스키마(`graph_verdict`, `relationship_findings[]`)
- 그래프/엣지/전파 규칙 원천: SkillScan `../../SkillScan/docs/ARCHITECTURE.md` §3

## 🔧 작업 (Tasks)

1. `skills/relationship-graph-analyzer/SKILL.md` 작성(기존 스킬과 동일 markdown 형식, 코드 실행 없음 — Claude 추론 지시문):
   - **노드 추출**: 대상에서 Plugin/Skill/Agent/Hook/MCPServer/Command 식별(plugin.json, SKILL.md/agent frontmatter, hooks.json, .mcp.json).
   - **엣지 발견 규칙**(표): `bundles`(plugin→자식), `delegates_to`(skill→agent), `preloads`(agent→skill), `uses_mcp`, `invokes_hook`, `references`(본문 이름 교차, 약함).
   - **위험 전파 규칙**(표): 신뢰 엣지를 따라 자식의 위험을 부모로 감쇠 전파(예: bundles 1.0, delegates_to 0.8, preloads/uses_mcp 0.7). 그래프 verdict = 전파 후 최악 노드.
   - **출력**: v1.3 `relationship_findings[]`(REL-NNN: 위험 노드/엣지/전파 경로) + summary `graph_verdict`.
   - **정적 원칙**: 대상 코드 미실행, 참조 추적은 그래프로(단계 제한 대신 순환 방지).
2. 한국어 예시 1건 포함(악성 에이전트를 번들한 플러그인 → 그래프 REMOVE 전파).

## ✅ 완료 조건 (Acceptance) — 검증 가능

- `skills/relationship-graph-analyzer/SKILL.md` 존재, 노드/엣지/전파/그래프verdict 산출 지시 + 예시 포함.
- 엣지 발견·전파 규칙이 표로 명시(결정적·재현 가능).
- 출력이 Phase 1 v1.3 필드(`relationship_findings`, `graph_verdict`)와 일치.
- "코드 실행 금지(정적)" 제약 명시.

## 🔗 선행 의존성

Phase 1.
