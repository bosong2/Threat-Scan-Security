---
name: prompt-optimizer
description: >
  Identify token-wasteful or poorly formatted prompts in skills and agents:
  redundant instructions, bloated schemas, and inconsistent formatting.
---

# Prompt Optimizer Skill

## 개요

토큰 낭비 및 비효율적 포맷팅을 식별하는 스킬.

## 역할

1. 과도한 공백 탐지
2. 반복되는 빈 줄 식별
3. 중복 프롬프트 블록 탐지
4. 토큰 사용량 최적화 권고

## 호출 방법

```
@prompt-optimizer <repository-path>
```

## 점검 항목

| 점검 항목 | 설명 |
|-----------|------|
| 과도한 공백 | 불필요한 공백 및 후행 공백 |
| 반복 빈 줄 | 연속된 빈 줄 (3줄 이상) |
| 중복 프롬프트 블록 | 반복되는 프롬프트 내용 |
| 비효율적 포맷팅 | 토큰 사용량 증가 요인 |

## 분석 대상 파일

```
**/*.md
**/SKILL.md
**/.cursor/rules/**
**/.github/copilot-instructions.md
**/prompts/**
**/templates/**
**/*.prompt
**/*.txt (프롬프트 관련)
```

## 비효율 패턴

### 1. 공백 관련
```markdown
# 문제: 과도한 후행 공백
This is a line with trailing spaces.    

# 문제: 불필요한 들여쓰기
    Unnecessarily indented text.

# 문제: 탭과 스페이스 혼용
	Mixed tabs and spaces.
```

### 2. 빈 줄 관련
```markdown
# 문제: 연속 빈 줄 (3줄 이상)
Line 1


Line 2
```

### 3. 중복 프롬프트
```markdown
# 문제: 동일 내용 반복
You must follow these rules:
- Rule A
- Rule B

...later in file...

You must follow these rules:
- Rule A
- Rule B
```

### 4. 비효율적 표현
```markdown
# 비효율
Please make sure to always ensure that you...

# 효율적
Ensure that...
```

## 토큰 낭비 패턴

| 패턴 | 예시 | 권장 |
|------|------|------|
| 과도한 정중함 | "Please kindly ensure that..." | "Ensure..." |
| 반복 강조 | "Very very important" | "Important" |
| 불필요한 수식 | "In order to" | "To" |
| 장황한 표현 | "At this point in time" | "Now" |
| 중복 설명 | 동일 규칙 반복 서술 | 한 번만 명시 |

## 출력 형식

```json
{
  "prompt_optimization": [
    {
      "id": "OPT-001",
      "file": "prompts/main.md",
      "issue": "Excessive Whitespace",
      "examples": "Lines 45-60: 12 trailing spaces, 3 consecutive blank lines",
      "severity": "Low",
      "recommendation": "Remove trailing spaces and reduce blank lines to maximum 2"
    }
  ]
}
```

## 토큰 추정 방식

대략적인 토큰 계산:
- 영문: ~4 characters = 1 token
- 한글: ~1.5 characters = 1 token
- 공백/특수문자: 개별 계산

### 절감 가능 토큰 계산
```
원본 파일 토큰: 1,500
최적화 후 예상: 1,200
절감: 300 tokens (20%)
```

## Deep Dive 기준

여러 파일에서 동일 패턴 발견 시 심층 분석:

### 분석 항목
1. 파일 간 중복 프롬프트 비교
2. 공통 패턴 추출
3. 중앙화 가능성 평가
4. 토큰 총 절감량 계산

## Severity 기준

| Severity | 기준 |
|----------|------|
| High | 대량 중복 (>500 tokens 절감 가능) |
| Medium | 중간 중복 (100-500 tokens 절감 가능) |
| Low | 경미한 비효율 (<100 tokens) |

## 최적화 권장사항

### 1. 공백 최적화
```bash
# 후행 공백 제거
sed -i 's/[[:space:]]*$//' file.md

# 연속 빈 줄 정리 (최대 2줄)
cat -s file.md > cleaned.md
```

### 2. 프롬프트 구조화
```markdown
# Before (비효율)
You should always remember to check the input.
You should always validate user data.
You should always sanitize strings.

# After (효율)
Always:
- Check input
- Validate user data  
- Sanitize strings
```

### 3. 중복 제거
```markdown
# Before (중복)
[파일A]: Follow coding standards.
[파일B]: Follow coding standards.
[파일C]: Follow coding standards.

# After (중앙화)
[공통 파일]: Follow coding standards.
[파일A/B/C]: @include(common.md)
```

## 제약 사항

- 의미적 중복 판단 한계
- 의도적 반복 구분 어려움
- 토큰 계산은 추정치

## 사용 예시

```
사용자: @prompt-optimizer /Users/user/project

응답:
[PROMPT_OPTIMIZATION]
file: .cursor/rules/main.md
issue: Duplicate Content Blocks
examples:
  - Lines 12-25: "You must follow security guidelines..."
  - Lines 145-158: Same content repeated
  - Lines 289-302: Same content repeated
severity: Medium
recommendation:
  1. 공통 내용을 별도 파일로 분리
  2. @include 또는 참조 방식 사용
  3. 예상 절감: ~200 tokens

토큰 분석 요약:
| 파일 | 현재 토큰 | 최적화 후 | 절감 |
|------|-----------|-----------|------|
| main.md | 2,500 | 2,100 | 400 |
| rules.md | 1,800 | 1,650 | 150 |
| Total | 4,300 | 3,750 | 550 |
```
