---
name: relationship-graph-analyzer
description: >
  Build a component relationship graph and propagate risk along trust edges
  to produce a graph-based security verdict (INSTALL_OK/REVIEW/DISABLE/REMOVE).
---

# Relationship Graph Analyzer

## 개요

컴포넌트 연관관계 그래프를 구축하고, 엣지를 따라 위험을 전파하여 그래프 기반 보안 verdict를 산출하는 스킬.
기존 `skill-security-analyzer`의 "최대 3단계 참조 추적"을 그래프 전파 방식으로 일반화한다.

**정적 분석 원칙**: 대상 코드를 실행하지 않는다. 참조 추적은 그래프 순회(사이클 방지)로 수행한다.

## 역할

1. 리포지토리에서 컴포넌트 노드 추출 (Plugin/Skill/Agent/Hook/MCPServer/Command)
2. 컴포넌트 간 의존성·위임 엣지 발견
3. 엣지 가중치 감쇠를 적용하여 위험 전파
4. 컴포넌트별 그래프 verdict 산출 + summary `graph_verdict`

## 호출 방법

```
@relationship-graph-analyzer <repository-path>
```

## 노드 추출 규칙

| 컴포넌트 타입 | 탐지 파일/패턴 |
|--------------|---------------|
| `Plugin` | `plugin.json`, `.claude-plugin/plugin.json`, `package.json`의 `claudePlugin` 필드 |
| `Skill` | `**/SKILL.md`, `**/skill.md`, 이름이 스킬 패턴인 `.md` 파일 |
| `Agent` | `**/agent.yaml`, `**/agent.json`, 에이전트 frontmatter를 가진 `.md` |
| `Hook` | `hooks.json`, `.claude/settings.json`의 `hooks` 필드, `PreToolUse`/`PostToolUse` 항목 |
| `MCPServer` | `.mcp.json`, `mcp.json`, `settings.json`의 `mcpServers` 필드 |
| `Command` | `.claude/commands/`, `commands/*.md` |

## 엣지 발견 규칙

| 엣지 타입 | 방향 | 탐지 방법 | 감쇠 가중치 |
|-----------|------|-----------|------------|
| `bundles` | Plugin → Child | `plugin.json`의 `skills`, `agents`, `commands` 배열 | 1.0 (전파 손실 없음) |
| `delegates_to` | Skill → Agent | SKILL.md 본문에서 `@agent-name` 참조 | 0.8 |
| `preloads` | Agent → Skill | agent yaml/frontmatter의 `skills` 또는 `preloaded_skills` | 0.7 |
| `uses_mcp` | Skill/Agent → MCPServer | SKILL.md/agent에서 MCP 서버 이름 참조 | 0.7 |
| `invokes_hook` | Plugin/Agent → Hook | hooks.json 또는 settings.json의 hook 매핑 | 0.6 |
| `references` | Any → Any | 본문 내 다른 컴포넌트 이름 약참조 (약한 엣지) | 0.5 |

**미해석 참조 처리**: 스캔 집합에 존재하지 않는 컴포넌트를 참조하면 `dangling_reference`로 기록하고 `REVIEW` verdict 부여.

## 위험 전파 알고리즘

```
1. 각 노드에 자체 severity→score 매핑:
   Critical=75, High=50, Medium=25, Low=10, Info=5, None=0

2. 엣지를 따라 하위 노드의 score × 감쇠 가중치를 상위 노드에 가산:
   propagated_score = own_score + Σ(child_score × edge_weight)
   (100 clamp 적용)

3. DAG 순회, 사이클 탐지 시 방문한 노드 1회 제한 + max-depth=10 가드.

4. 최종 score → verdict 재매핑:
   score ≥ 75 → REMOVE
   score ≥ 50 → DISABLE
   score ≥ 25 → REVIEW
   score < 25  → INSTALL_OK
```

## Severity → Score → Verdict 매핑 요약

| Severity | 자체 Score | Security Verdict |
|----------|-----------|-----------------|
| `Critical` | 75 | `REMOVE` |
| `High` | 50 | `DISABLE` |
| `Medium` | 25 | `REVIEW` |
| `Low` | 10 | `INSTALL_OK` |
| `Info` / `None` | 5 / 0 | `INSTALL_OK` |

**모델 강등 규칙**: `model_effectiveness`가 `OBSOLETE` 또는 `MODEL_LOCKED`이면 해당 노드의 `INSTALL_OK`를 `REVIEW`로 강등한다.

## 출력 형식

```json
{
  "relationship_findings": [
    {
      "id": "REL-001",
      "component": "my-plugin",
      "component_type": "Plugin",
      "edge_type": "bundles",
      "target_component": "malicious-agent",
      "target_type": "Agent",
      "propagated_risk": "REMOVE",
      "own_severity": "Low",
      "severity": "Critical",
      "issue": "Plugin bundles an agent rated REMOVE; risk propagated via bundles edge (weight 1.0).",
      "propagation_path": [
        "my-plugin --bundles(1.0)--> malicious-agent (REMOVE, score=75)"
      ],
      "recommendation": "Remove malicious-agent from the plugin bundle. Review bundled agent list in plugin.json.",
      "verdict": "REMOVE"
    },
    {
      "id": "REL-002",
      "component": "data-skill",
      "component_type": "Skill",
      "edge_type": "uses_mcp",
      "target_component": "unrestricted-mcp-server",
      "target_type": "MCPServer",
      "propagated_risk": "DISABLE",
      "own_severity": "Low",
      "severity": "High",
      "issue": "Skill delegates to an MCP server rated DISABLE; propagated risk elevates skill to DISABLE.",
      "propagation_path": [
        "data-skill --uses_mcp(0.7)--> unrestricted-mcp-server (DISABLE, score=50)"
      ],
      "recommendation": "Restrict MCP server permissions or replace with a sandboxed alternative.",
      "verdict": "DISABLE"
    }
  ],
  "graph_verdict": {
    "security_verdict": "REMOVE",
    "worst_component": "malicious-agent",
    "rationale": "malicious-agent (REMOVE) is bundled by my-plugin, propagating Critical risk to the plugin via bundles edge (weight 1.0)."
  }
}
```

## 한국어 예시 — 악성 에이전트 번들 시나리오

**상황**: `security-plugin`이 `data-exfil-agent`를 번들로 포함하고 있고, `data-exfil-agent`는 외부 데이터 전송 위험으로 Critical 판정을 받았다.

**그래프 구조**:
```
security-plugin (Low) --bundles(1.0)--> data-exfil-agent (Critical, score=75)
```

**전파 결과**:
- `security-plugin` 자체 score: 10 (Low)
- `data-exfil-agent` 기여: 75 × 1.0 = 75
- `security-plugin` 최종 score: min(85, 100) = 85 → **REMOVE**

**REL finding 산출**:
```json
{
  "id": "REL-001",
  "component": "security-plugin",
  "component_type": "Plugin",
  "edge_type": "bundles",
  "target_component": "data-exfil-agent",
  "target_type": "Agent",
  "propagated_risk": "REMOVE",
  "own_severity": "Low",
  "severity": "Critical",
  "issue": "플러그인이 외부 데이터 전송 위험(Critical)으로 분류된 에이전트를 번들에 포함하고 있음. bundles 엣지(가중치 1.0)를 통해 위험이 전파되어 플러그인도 REMOVE 판정.",
  "propagation_path": [
    "security-plugin --bundles(1.0)--> data-exfil-agent (REMOVE, score=75)"
  ],
  "recommendation": "plugin.json에서 data-exfil-agent를 제거하고 에이전트 자체를 별도 보안 검토 후 교체하십시오.",
  "verdict": "REMOVE"
}
```

## 분석 경계 및 제약 사항

- **코드 실행 금지**: 탐지는 파일 구조/텍스트 참조만으로 수행
- **사이클 방지**: DAG 순회 시 이미 방문한 노드는 1회 방문 + max-depth=10 가드
- **약참조(references) 엣지**: 본문 내 텍스트 언급 기반으로, 실제 의존성이 아닐 수 있음 — 반드시 근거 인용
- **스캔 집합 외 컴포넌트**: `dangling_reference`로 기록, `REVIEW` 부여 — 외부 패키지이거나 경로 불일치 가능성 명시

## 스키마 참조

출력은 `docs/claude-threat-scan-json-schema-v1.3.md` §13 `relationship_findings[]` 및 §4 `graph_verdict` 규격을 따른다.
ID 형식: `REL-NNN`. 모든 찾기 verdict는 대문자 4종 중 하나.
