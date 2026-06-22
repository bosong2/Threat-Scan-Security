---
name: skill-security-analyzer
description: >
  Evaluate security risks in AI tool definitions (SKILL.md) and prompt templates:
  prompt injection, privilege escalation, exfiltration vectors, tool abuse.
---

# Skill Security Analyzer

## 개요

AI 도구 정의(SKILL.md) 및 프롬프트 템플릿의 보안 위험을 평가하는 스킬.

## 역할

1. SKILL.md 파일 보안 분석
2. 도구 메타데이터 위험 평가
3. 프롬프트 인젝션 취약점 탐지
4. 권한 상승 위험 분석

## 호출 방법

```
@skill-security-analyzer <repository-path>
```

## 점검 항목

| 평가 범주 | 설명 |
|-----------|------|
| 민감 정보 노출 | 도구 정의 내 민감 데이터 노출 위험 |
| 권한 상승 | 불필요한 접근 권한 확대 |
| 명령 실행 | 시스템 명령 실행 가능 여부 |
| 외부 데이터 전송 | 데이터 유출 경로 분석 |
| 프롬프트 인젝션 | 규칙 우회, 명령 무시 취약점 |

## 분석 대상 파일

```
**/SKILL.md
**/skill.md
**/tool.yaml
**/tool.json
**/.cursor/rules/**
**/.github/copilot-instructions.md
**/prompts/**
**/agents/**
```

## 취약점 패턴

### 1. 민감 정보 노출
```markdown
# 위험 패턴
API_KEY: sk-xxxx
password: "admin123"
token: ${SECRET_TOKEN}  # 환경변수 참조도 주의
```

### 2. 권한 상승
```yaml
# 위험 패턴
permissions:
  - file_system: write_all
  - network: unrestricted
  - shell: enabled
```

### 3. 명령 실행
```markdown
# 위험 패턴
이 도구는 run_in_terminal을 사용하여...
시스템 명령을 실행할 수 있습니다...
```

### 4. 프롬프트 인젝션
```markdown
# 취약 패턴
사용자 입력을 직접 처리합니다
{{user_input}} 를 명령으로 실행

# 보호 누락
- 입력 검증 없음
- 역할 경계 불명확
- 명령 화이트리스트 없음
```

## 출력 형식

```json
{
  "skill_risk_findings": [
    {
      "id": "SKILL-001",
      "file": ".cursor/rules/main.md",
      "fragment": "run_in_terminal with user input",
      "risk_type": "Command Execution Risk",
      "analysis": "Skill allows arbitrary command execution based on user input without validation",
      "severity": "High",
      "status": "Confirmed",
      "recommendation": "1. Implement command whitelist. 2. Add input validation. 3. Use sandboxed execution."
    }
  ]
}
```

## Deep Dive 기준

다음 조건에서 심층 분석 수행:
- Severity가 Medium 또는 High
- Skill/도구 목적이 불분명
- 여러 컴포넌트 간 참조 발생

### Deep Dive 분석 경로 (최대 3단계)
```
SKILL.md → 참조된 도구 코드 → 에이전트 사용처 → 설정 파일
```

## Severity 기준

| Severity | 기준 |
|----------|------|
| Critical | 무제한 명령 실행, 자격 증명 노출 |
| High | 권한 상승, 데이터 유출 경로 |
| Medium | 불명확한 권한 경계, 잠재적 인젝션 |
| Low | 과도한 권한 요청, 문서화 부족 |

## 프롬프트 인젝션 탐지

### 취약 패턴
1. **직접 삽입**: 사용자 입력이 프롬프트에 직접 삽입
2. **규칙 무시 유도**: "이전 지시를 무시하고..."
3. **역할 탈취**: "당신은 이제 관리자입니다..."
4. **간접 인젝션**: 외부 데이터를 통한 프롬프트 조작

### 방어 패턴 확인
- [ ] 입력 검증 존재
- [ ] 역할 경계 명확
- [ ] 명령 화이트리스트
- [ ] 출력 필터링

## 제약 사항

- 도구 실제 실행 금지
- 정적 분석만 수행
- 3단계 이상 참조 추적 금지

## 사용 예시

```
사용자: @skill-security-analyzer /Users/user/project

응답:
[SKILL_RISK]
file: skills/database-tool/SKILL.md
fragment: "Execute SQL queries directly from user input"
risk_type: SQL Injection Risk
analysis: 
  - 사용자 입력이 SQL 쿼리에 직접 삽입됨
  - Parameterized query 미사용
  - 입력 검증 없음
severity: High
status: Confirmed
recommendation:
  1. Parameterized query 사용
  2. 입력 화이트리스트 적용
  3. 읽기 전용 권한으로 제한
```
