---
name: agent-policy-verifier
description: >
  Verify security policy compliance of AI agents: tool grants, permission
  boundaries, least-privilege adherence, policy file presence and correctness.
---

# Agent Policy Verifier Skill

## 개요

AI 에이전트의 보안 정책 적용 상태를 검증하는 스킬.

## 역할

1. `disallowed_tools` 정책 정의 여부 확인
2. 위험 도구의 암묵적 허용 탐지
3. 에이전트 간 정책 일관성 검증
4. 중앙 정책 재사용 권고

## 호출 방법

```
@agent-policy-verifier <repository-path>
```

## 점검 항목

| 점검 항목 | 설명 |
|-----------|------|
| `disallowed_tools` 정책 | 위험 도구 사용 제한 정책 정의 여부 |
| 암묵적 허용 | 위험 도구의 암묵적 허용 여부 |
| 정책 일관성 | 에이전트 간 정책 불일치 |
| 중앙 정책 재사용 | 정책 표준화 권고 |

## 분석 대상 파일

```
**/agent.yaml
**/agent.json
**/agents/**
**/.cursor/agents/**
**/.github/agents/**
**/copilot-agents.yaml
```

## 위험 도구 분류

### Critical 위험 도구
```yaml
critical_tools:
  - execute_command
  - run_shell
  - run_in_terminal
  - system_exec
  - eval_code
  - write_file_system
  - delete_file
  - modify_system
```

### High 위험 도구
```yaml
high_risk_tools:
  - network_request
  - http_client
  - send_email
  - upload_file
  - database_write
  - create_user
  - modify_permissions
```

### Medium 위험 도구
```yaml
medium_risk_tools:
  - file_read
  - database_read
  - list_directory
  - get_env_variable
  - cache_write
```

## 정책 검증 기준

### 1. 필수 정책 항목
```yaml
# 권장 구조
agent:
  name: "agent-name"
  security_policy:
    disallowed_tools:
      - execute_command
      - write_file
    allowed_tools:
      - read_file
      - search_code
    permission_level: "restricted"
    sandbox_mode: true
```

### 2. 정책 일관성 검사
- 동일 조직 내 에이전트 간 정책 비교
- 상위 정책 상속 여부
- 예외 처리 명시 여부

### 3. 암묵적 허용 탐지
```yaml
# 위험: disallowed_tools 미정의
agent:
  name: "data-agent"
  tools:
    - read_database
    - execute_command  # 암묵적 허용됨 - 위험!
```

## 출력 형식

⚠️ **필수: Schema V1.2 엄격 준수** - [SCHEMA_V1.2_ENFORCEMENT.md](../../docs/SCHEMA_V1.2_ENFORCEMENT.md) 참조

```json
{
  "agent_policy_findings": [
    {
      "id": "AGENT-001",
      "file": "agents/data-agent.yaml",
      "agent": "DataProcessingAgent",
      "issue": "No disallowed_tools policy defined",
      "disallowed_tools": ["execute_command", "write_file", "network_request"],
      "severity": "Medium",
      "recommendation": "Define explicit disallowed_tools list with critical and high-risk tools"
    }
  ]
}
```

### ❌ 절대 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `finding_id` | `id` |
| `location` | `file` |
| `title` | `issue` |
| `remediation` | `recommendation` |
| severity 소문자 | 대문자 시작 |
```

## Deep Dive 기준

다음 조건에서 심층 분석 수행:
- 정책 미정의 에이전트 발견
- 위험 도구 암묵적 허용
- 정책 간 불일치 발견

### 분석 경로 (최대 3단계)
```
에이전트 정의 → 도구 설정 → 정책 파일 → Skill 정의
```

## 권장 정책 템플릿

```yaml
# 보안 에이전트 정책 템플릿
security_policy:
  version: "1.0"
  
  # 절대 허용 불가
  disallowed_tools:
    - execute_command
    - run_shell
    - eval_code
    - delete_file
    - modify_system
  
  # 조건부 허용 (감사 로그 필요)
  audited_tools:
    - write_file
    - network_request
    - database_write
  
  # 자유 사용 가능
  allowed_tools:
    - read_file
    - search_code
    - list_directory
  
  # 실행 제약
  constraints:
    sandbox_mode: true
    network_isolation: true
    max_execution_time: 30s
    resource_limits:
      memory: "512MB"
      cpu: "0.5"
```

## Severity 기준

| Severity | 기준 |
|----------|------|
| Critical | 무제한 명령 실행 허용 |
| High | 위험 도구 암묵적 허용, 정책 완전 부재 |
| Medium | 부분적 정책 정의, 일부 위험 도구 허용 |
| Low | 정책 불일치, 문서화 부족 |

## 제약 사항

- 에이전트 실제 실행 금지
- 정적 설정 분석만 수행
- 동적 정책 변경 감지 불가

## 사용 예시

```
사용자: @agent-policy-verifier /Users/user/project

응답:
[AGENT_POLICY_RISK]
file: agents/assistant-agent.yaml
agent: AssistantAgent
issue: Critical tools implicitly allowed
analysis:
  - disallowed_tools 정책 미정의
  - 도구 목록에 execute_command 포함
  - sandbox_mode 비활성화
severity: High
recommendation:
  1. disallowed_tools 정책 추가
  2. execute_command 제거 또는 제한
  3. sandbox_mode 활성화

정책 비교:
| Agent | disallowed_tools | sandbox | 일관성 |
|-------|------------------|---------|--------|
| CodeAgent | ✓ 정의됨 | ✓ | - |
| DataAgent | ✗ 미정의 | ✗ | 불일치 |
| AssistantAgent | ✗ 미정의 | ✗ | 불일치 |
```
