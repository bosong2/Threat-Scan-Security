# Claude Threat Scan JSON Schema Specification v1.3

본 문서는 `security-report-viewer-claude.html` 뷰어와 호환되는 JSON 출력 규격을 정의한다.

**V1.3 변경사항**: 컴포넌트 연관관계 그래프·위험 전파, 모델 유효성/진부화 판정, 조치 verdict 체계 추가.
모든 신규 필드는 **optional**이므로 v1.2 페이로드는 v1.3에서 그대로 유효하다.

---

## 1. Root Structure

```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",
  "scan_metadata": {},
  "english_report": {},
  "korean_report": {}
}
```

모든 필드는 **필수**이다.

---

## 2. scan_metadata

```json
"scan_metadata": {
  "scan_date": "2026-01-06T12:00:00Z",
  "scanner_version": "Claude Threat Scan V2.1",
  "repository": "project-name",
  "target_repository": "project-name",
  "total_files_scanned": 32,
  "total_files": 32,
  "code_files": 8,
  "analysis_depth": 3,
  "scan_depth": 3
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scan_date` | string | ✓ | ISO 8601 형식 |
| `scanner_version` | string | ✓ | 스캐너 버전 (V2.1+) |
| `repository` | string | ✓ | 저장소명 (짧은 이름) |
| `target_repository` | string | ✓ | 대상 저장소명 (뷰어 표시용) |
| `total_files_scanned` | number | ✓ | 스캔된 전체 파일 수 |
| `total_files` | number | ✓ | 전체 파일 수 (뷰어 summary card) |
| `code_files` | number | ✓ | 코드 파일 수 |
| `analysis_depth` | number | ✓ | 분석 깊이 (1-3) |
| `scan_depth` | number | ✓ | 스캔 깊이 (뷰어 표시용) |

---

## 3. english_report / korean_report Structure

```json
"english_report": {
  "repository_summary": {},
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
```

**V1.3 추가 (all optional)**:
- `relationship_findings` 배열 — 컴포넌트 연관관계 그래프 분석 결과
- `model_validity_findings` 배열 — 모델 유효성/진부화 판정 결과

---

## 4. repository_summary (V1.3 확장)

```json
"repository_summary": {
  "description": "Project description here",
  "file_statistics": {
    "total_files": 32,
    "python_files": 0,
    "javascript_files": 1,
    "typescript_tsx": 7,
    "markdown_files": 6,
    "json_files": 4,
    "pem_files": 0,
    "yaml": 1,
    "css": 1,
    "svg": 5,
    "html": 1,
    "other": 6
  },
  "key_components": [
    "Component 1",
    "Component 2"
  ],
  "sensitive_files_detected": [],
  "graph_verdict": {
    "security_verdict": "REVIEW",
    "worst_component": "malicious-agent",
    "rationale": "Plugin bundles an agent rated REMOVE; propagated risk elevates plugin to DISABLE."
  }
}
```

**V1.3 추가**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `graph_verdict` | object | ○ | 그래프 전파 후 최악 컴포넌트 기준 summary verdict |
| `graph_verdict.security_verdict` | string | ○ | `INSTALL_OK` \| `REVIEW` \| `DISABLE` \| `REMOVE` |
| `graph_verdict.worst_component` | string | ○ | 최악 판정을 받은 컴포넌트 이름 |
| `graph_verdict.rationale` | string | ○ | 판정 근거 (전파 경로 포함) |

---

## 5. Verdict 체계 (V1.3 신규)

### 5.1 Security Verdict — 보안/그래프 verdict

모든 finding 및 컴포넌트 수준에서 **optional** `verdict` 필드로 표현된다.

| Verdict | 의미 | 권장 조치 |
|---------|------|-----------|
| `INSTALL_OK` | 위험 없음, 설치 허용 | 정상 사용 |
| `REVIEW` | 검토 후 결정 권장 | 사용 전 담당자 검토 |
| `DISABLE` | 즉시 비활성화 권장 | 조치 완료 전 사용 중단 |
| `REMOVE` | 즉시 제거 권장 | 제거 후 대체제 검토 |

**severity → verdict 매핑 (결정론적)**:

| Severity | Security Verdict |
|----------|-----------------|
| `Critical` | `REMOVE` |
| `High` | `DISABLE` |
| `Medium` | `REVIEW` |
| `Low` / `Info` | `INSTALL_OK` |

**그래프 전파 규칙**:
- 그래프 verdict = 해당 컴포넌트 + 전파된 자식 노드들 중 가장 나쁜 verdict.
- 가중치 감쇠: `bundles` 엣지 ×1.0, `delegates_to` ×0.8, `preloads`/`uses_mcp` ×0.7, `references` (약참조) ×0.5.
- 모델 강등 규칙: `model_effectiveness`가 `OBSOLETE` 또는 `MODEL_LOCKED`이면 해당 컴포넌트의 `INSTALL_OK`를 `REVIEW`로 강등.

### 5.2 Model Effectiveness Verdict — 모델 유효성 verdict

컴포넌트/finding 수준에서 **optional** `model_effectiveness` 필드로 표현된다.

| Verdict | 의미 |
|---------|------|
| `VALID` | 현행 모델에서 의도한 대로 동작 |
| `DEGRADED` | 현행 모델에서 부분적으로 동작하나 효과 감소 |
| `OBSOLETE` | 현행 모델이 해당 기능을 네이티브로 수행 → 스킬 불필요 |
| `MODEL_LOCKED` | 은퇴/특정 모델에 고정 → 다른 모델에서 동작 불가 |

---

## 6. static_code_findings (V1.3 확장)

```json
{
  "id": "STATIC-001",
  "file": ".cursor/config.json",
  "line": 9,
  "issue": "Hardcoded Credential Placeholder",
  "description": "Contains placeholder string which could be replaced with real credentials.",
  "severity": "High",
  "status": "Confirmed",
  "deep_dive_result": "File is not in .gitignore. HIGH RISK if token is added.",
  "recommendation": "Add .cursor/config.json to .gitignore immediately.",
  "verdict": "DISABLE"
}
```

**V1.3 추가**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verdict` | string | ○ | `INSTALL_OK` \| `REVIEW` \| `DISABLE` \| `REMOVE` |

---

## 7. binary_analysis_findings (V1.3 확장)

```json
{
  "id": "BIN-001",
  "file": "dist/app.pyc",
  "behaviors": ["Network communication", "File system access"],
  "risk_summary": "Compiled Python file with network capabilities detected.",
  "severity": "Medium",
  "verdict": "REVIEW"
}
```

**V1.3 추가**: `verdict` (optional)

---

## 8. skill_risk_findings (V1.3 확장)

```json
{
  "id": "SKILL-001",
  "file": "skills/data-tool/SKILL.md",
  "fragment": "Execute SQL from user input",
  "risk_type": "SQL Injection Risk",
  "analysis": "User input inserted directly into SQL without validation.",
  "severity": "High",
  "status": "Confirmed",
  "recommendation": "Use parameterized queries.",
  "verdict": "DISABLE",
  "model_effectiveness": "VALID"
}
```

**V1.3 추가**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verdict` | string | ○ | Security verdict |
| `model_effectiveness` | string | ○ | Model effectiveness verdict |

---

## 9. agent_policy_findings (V1.3 확장)

```json
{
  "id": "AGENT-001",
  "file": "agents/data-agent.yaml",
  "agent": "DataProcessingAgent",
  "issue": "No disallowed_tools policy defined.",
  "disallowed_tools": ["execute_command", "write_file"],
  "severity": "Medium",
  "recommendation": "Define explicit disallowed_tools list.",
  "verdict": "REVIEW"
}
```

**V1.3 추가**: `verdict` (optional)

---

## 10. sensitive_patterns

```json
{
  "id": "SENS-001",
  "file": ".cursor/config.json",
  "pattern": "access-token",
  "detail": "Placeholder token detected.",
  "severity": "Medium",
  "status": "Potential Risk",
  "gitignore_status": "Not in .gitignore - RISK",
  "verdict": "REVIEW"
}
```

**V1.3 추가**: `verdict` (optional)

---

## 11. prompt_optimization

```json
{
  "id": "OPT-001",
  "file": "skills/main/SKILL.md",
  "issue": "Obsolete Chain-of-Thought Scaffolding",
  "examples": "Explicit step-by-step reasoning prompt that newer models handle natively.",
  "severity": "Low",
  "recommendation": "Remove manual CoT scaffolding; rely on model's native reasoning.",
  "verdict": "INSTALL_OK",
  "model_effectiveness": "OBSOLETE"
}
```

**V1.3 추가**: `verdict` (optional), `model_effectiveness` (optional)

---

## 12. sbom_analysis

V1.2와 동일. 변경 없음. (개별 finding에 `verdict` optional 추가 가능)

---

## 13. relationship_findings[] (NEW in V1.3)

컴포넌트 연관관계 그래프 분석 결과. **optional 배열**.

```json
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
  "issue": "Plugin bundles a high-risk agent; risk propagated via bundles edge.",
  "propagation_path": ["my-plugin --bundles--> malicious-agent (REMOVE)"],
  "recommendation": "Remove malicious-agent from plugin bundle.",
  "verdict": "REMOVE"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | 형식: `REL-NNN` |
| `component` | string | ✓ | 분석 대상 컴포넌트 이름 |
| `component_type` | string | ✓ | `Plugin` \| `Skill` \| `Agent` \| `Hook` \| `MCPServer` \| `Command` |
| `edge_type` | string | ✓ | `bundles` \| `delegates_to` \| `preloads` \| `uses_mcp` \| `invokes_hook` \| `references` |
| `target_component` | string | ✓ | 연결 대상 컴포넌트 이름 |
| `target_type` | string | ✓ | 대상 컴포넌트 타입 |
| `propagated_risk` | string | ○ | 전파된 위험 verdict |
| `own_severity` | string | ○ | 자체 severity (전파 전) |
| `severity` | string | ✓ | 최종 severity (전파 반영) |
| `issue` | string | ✓ | 이슈 설명 |
| `propagation_path` | array | ○ | 전파 경로 문자열 배열 |
| `recommendation` | string | ✓ | 권장 조치 |
| `verdict` | string | ○ | Security verdict |

---

## 14. model_validity_findings[] (NEW in V1.3)

모델 유효성/진부화 판정 결과. **optional 배열**.

```json
{
  "id": "MODEL-001",
  "file": "skills/data-analyzer/SKILL.md",
  "component": "data-analyzer",
  "pattern_type": "MC1",
  "issue": "Hardcoded Retired Model ID",
  "evidence": "claude-instant-1 is listed in retired_model_ids registry.",
  "registry_field": "retired_model_ids",
  "severity": "High",
  "recommendation": "Replace claude-instant-1 with a current model ID or remove the hardcoded reference.",
  "verdict": "DISABLE",
  "model_effectiveness": "MODEL_LOCKED"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | 형식: `MODEL-NNN` |
| `file` | string | ✓ | 파일 경로 |
| `component` | string | ✓ | 컴포넌트 이름 |
| `pattern_type` | string | ✓ | `MC1` \| `MC2` \| `MC3` \| `MC4` \| `OB1` |
| `issue` | string | ✓ | 이슈 제목 |
| `evidence` | string | ✓ | 판정 근거 (registry 필드 인용 포함) |
| `registry_field` | string | ○ | 참조한 model-capabilities.json 필드 |
| `severity` | string | ✓ | `Critical` \| `High` \| `Medium` \| `Low` |
| `recommendation` | string | ✓ | 권장 조치 |
| `verdict` | string | ○ | Security verdict |
| `model_effectiveness` | string | ✓ | `VALID` \| `DEGRADED` \| `OBSOLETE` \| `MODEL_LOCKED` |

**pattern_type 설명**:

| Code | 의미 |
|------|------|
| `MC1` | 하드코딩/은퇴 모델 ID |
| `MC2` | 컨텍스트 윈도우 가정 (현행 모델과 불일치) |
| `MC3` | 폐기된 API 패턴 (budget_tokens 등) |
| `MC4` | 모델 한계 우회 지시 (현행 모델 불필요) |
| `OB1` | 진부화 힌트 (CoT 강제, 형식 강제, 청크 우회 등) |

---

## 15. recommendations ⚠️ CRITICAL

**V1.3.1 보강** — 추적성 필드(`id`, `rank`, `finding_ids`)를 추가하고 `priority` 타입을 명확히 한다. 신규 필드는 **모두 optional**(v1.2/v1.3 페이로드 하위호환).

```json
{
  "id": "REC-001",
  "rank": 1,
  "priority": "Critical",
  "category": "Secret Management",
  "action": "Remove plaintext credential auto-login (LOGIN_EMAIL / LOGIN_PASSWORD)",
  "rationale": "Plaintext passwords in environment variables are exposed via /proc, CI logs, and container inspection.",
  "finding_ids": ["STATIC-001", "SENS-001"],
  "affected_files": ["src/config.ts", ".gitignore"]
}
```

### 필드 정의

| Field | Type | Required | 규칙 |
|-------|------|----------|------|
| `id` | string | ✓ | `REC-NNN` 형식 (§17 참조) |
| `rank` | integer | ✓ | 처리 순서, 1부터 시작 (1=최우선). **순서는 여기에만 쓴다.** |
| `priority` | string | ✓ | `Critical`/`High`/`Medium`/`Low` — **문자열만. 정수 금지.** |
| `category` | string | ○ | 분류 (번역 대상) |
| `action` | string | ✓ | 권장 조치 (번역 대상) |
| `rationale` | string | ✓ | 근거 설명 (번역 대상) |
| `finding_ids` | string[] | ✓ | 근거 finding ID 목록. **기존 finding의 id만 참조**, 빈 배열 금지(최소 1개). |
| `affected_files` | string[] | ○ | 영향 파일 목록 |

### ⚠️ 핵심 규칙

- **`priority`는 문자열 심각도다. 정수(1~7)를 넣지 마라.** 처리 순서가 필요하면 `rank`(정수)를 사용한다. (순서 vs 등급 — 두 개념을 분리한다.)
- **`priority` 산정**: 해당 권장이 참조하는 `finding_ids` 들의 **최고 severity**.
- **`rank` 산정**: priority 내림차순 정렬 순번.
- **`finding_ids`**: 권장이 어느 finding에서 파생됐는지의 역참조. 보고서 내 실제 존재하는 finding ID만 넣는다(STATIC-NNN, SENS-NNN, REL-NNN 등).
- 신규 필드(`id`/`rank`/`finding_ids`)는 optional이므로, 이 필드들이 없는 기존 v1.2/v1.3 페이로드도 유효하다.

---

## 16. Severity Values

유효한 severity 값:
- `Critical` - 즉시 조치 필요
- `High` - 우선 조치 필요
- `Medium` - 계획된 조치 필요
- `Low` - 개선 권장
- `Info` - 정보성 (sensitive_patterns에서만 사용)
- `None` - 해당 없음

---

## 17. ID Naming Convention

| Section | Format | Example |
|---------|--------|---------|
| static_code_findings | `STATIC-NNN` | `STATIC-001` |
| binary_analysis_findings | `BIN-NNN` | `BIN-001` |
| skill_risk_findings | `SKILL-NNN` | `SKILL-001` |
| agent_policy_findings | `AGENT-NNN` | `AGENT-001` |
| sensitive_patterns | `SENS-NNN` | `SENS-001` |
| prompt_optimization | `OPT-NNN` | `OPT-001` |
| vulnerability_findings | `VULN-NNN` | `VULN-001` |
| license_findings | `LIC-NNN` | `LIC-001` |
| version_risk_findings | `VER-NNN` | `VER-001` |
| supply_chain_findings | `SUPPLY-NNN` | `SUPPLY-001` |
| relationship_findings | `REL-NNN` | `REL-001` |
| model_validity_findings | `MODEL-NNN` | `MODEL-001` |
| recommendations | `REC-NNN` | `REC-001` |

---

## 18. Common Mistakes to Avoid

| ❌ Wrong | ✓ Correct |
|----------|-----------|
| `dangerous_files_found` | `sensitive_files_detected` |
| `description` (in recommendations) | `rationale` |
| `affected_file` | `affected_files` (배열) |
| severity 소문자 | severity **첫 글자 대문자** |
| `javascriptFiles` | `javascript_files` |
| `vulnerabilityFindings` | `vulnerability_findings` |
| verdict 소문자 (`remove`) | verdict **대문자** (`REMOVE`) |
| model_effectiveness 소문자 | model_effectiveness **대문자** (`OBSOLETE`) |
| `recommendations[].priority` 정수 (1~7) | `priority` **문자열**(Critical/High/…) + 순서는 `rank` 정수 |
| recommendations에 `id`/`finding_ids` 누락 | `id`(REC-NNN) + `finding_ids`(근거 finding 참조) 포함 |
| `deep_dive_result` 객체 | `deep_dive_result` **문자열** (멀티라인 `\n` 허용) |
| `code_snippet` (자유서술) | 금지 유지 — deep-dive 수정 코드는 `code_fix` 구조화 필드 |
| 코드를 prose/recommendation에 삽입 | 코드는 `code_fix.before/after`에만 (JSON 문자열 이스케이프) |

---

## 18.5 Deep Dive 필드 (finding 공통, optional)

Deep Dive(심층 분석)가 Medium↑ finding에 채우는 optional 필드. 상세·JSON 안전 규칙은 `SCHEMA_V1.3_ENFORCEMENT.md` §2.7 참조.

```json
{
  "id": "STATIC-001",
  "status": "Confirmed",
  "deep_dive_result": "Level 1: ... Level 2: ... Level 3: ... 결론: Confirmed.",
  "code_fix": {
    "language": "typescript",
    "before": "const cmd = `mmdc -i ${userInput}`;\nexec(cmd);",
    "after": "execFile('mmdc', ['-i', userInput]);",
    "note": "Use execFile to avoid shell interpolation."
  }
}
```

| 필드 | 타입 | 비고 |
|------|------|------|
| `status` | string | Confirmed/Mitigated/False Positive/Potential Risk |
| `deep_dive_result` | string | 3단계 분석 서술(객체 금지, 줄바꿈 허용) |
| `code_fix` | object | `{language, before?, after, note?}` — 수정 코드는 여기에만 격리 |

**핵심**: 모든 코드는 JSON 문자열 값으로만 존재(`\n`/`\"`/`\\` 이스케이프). 마크다운 코드펜스 금지. `code_snippet`(금지)과 `code_fix`(승인) 구분.

---

## 19. Validation Checklist

### 기본 필드 (V1.1)
- [ ] `scan_metadata.target_repository` 존재
- [ ] `scan_metadata.total_files` 존재
- [ ] `scan_metadata.code_files` 존재
- [ ] `scan_metadata.scan_depth` 존재
- [ ] `repository_summary.sensitive_files_detected` 사용 (NOT `dangerous_files_found`)
- [ ] `repository_summary.file_statistics.python_files` 존재
- [ ] `repository_summary.file_statistics.javascript_files` 존재
- [ ] `recommendations[].action` 존재
- [ ] `recommendations[].rationale` 존재
- [ ] 모든 severity 값 첫 글자 대문자

### SBOM 필드 (V1.2)
- [ ] `sbom_analysis` 객체 존재
- [ ] 모든 SBOM finding ID 형식 준수

### V1.3 신규 필드 (optional — 존재하는 경우에만 형식 검증)
- [ ] `relationship_findings[].id` 형식: `REL-NNN`
- [ ] `model_validity_findings[].id` 형식: `MODEL-NNN`
- [ ] `graph_verdict.security_verdict` ∈ {`INSTALL_OK`,`REVIEW`,`DISABLE`,`REMOVE`} (존재 시)
- [ ] 각 finding `verdict` ∈ {`INSTALL_OK`,`REVIEW`,`DISABLE`,`REMOVE`} (존재 시)
- [ ] `model_effectiveness` ∈ {`VALID`,`DEGRADED`,`OBSOLETE`,`MODEL_LOCKED`} (존재 시)
- [ ] severity→verdict 매핑 일관성 (Critical→REMOVE, High→DISABLE, Medium→REVIEW, Low→INSTALL_OK)
- [ ] model_validity_findings[].model_effectiveness 필수 존재

---

## 20. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-31 | Initial specification |
| 1.1 | 2026-01-05 | Added viewer compatibility fields, fixed field naming conventions |
| 1.2 | 2026-01-06 | Added SBOM analysis section |
| 1.3 | 2026-06-22 | Added: verdict system (INSTALL_OK/REVIEW/DISABLE/REMOVE), model_effectiveness (VALID/DEGRADED/OBSOLETE/MODEL_LOCKED), relationship_findings[] (REL-NNN), model_validity_findings[] (MODEL-NNN), graph_verdict in summary. All new fields optional — v1.2 payloads remain valid. |
