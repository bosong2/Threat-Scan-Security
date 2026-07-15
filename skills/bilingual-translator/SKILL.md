---
name: bilingual-translator
description: >
  Translate the English security scan report into Korean using the standard
  security terminology dictionary, producing the final bilingual JSON report.
---

# Bilingual Translator Skill

## 개요

영문 보안 스캔 결과를 한글로 번역하여 bilingual JSON 보고서를 생성하는 전문 번역 스킬.

## 역할

1. 영문 스캔 결과 수신
2. 표준 보안 용어 사전 참조
3. 일관된 한글 번역 수행
4. bilingual JSON 보고서 생성

## 호출 방법

```
@bilingual-translator <english-report> [--lang ko]
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--lang` | 대상 언어 코드 | `ko` |
| `--dict` | 사용자 정의 사전 경로 | 내장 사전 |

## 지원 언어

| 코드 | 언어 | 상태 |
|------|------|------|
| `ko` | 한국어 | ✓ 지원 |
| `ja` | 日本語 | 예정 |
| `zh-CN` | 简体中文 | 예정 |
| `zh-TW` | 繁體中文 | 예정 |
| `es` | Español | 예정 |
| `de` | Deutsch | 예정 |

## 참조 용어 사전

### 표준 출처
| 표준 | 설명 |
|------|------|
| NIST Glossary | 10,000+ 보안 용어 (https://csrc.nist.gov/glossary) |
| NIST CSF 2.0 | Cybersecurity Framework |
| CIS Controls v8.1 | Critical Security Controls |
| ISO 27001:2022 | 정보보안 관리체계 |
| OWASP | 웹 애플리케이션 보안 |
| KISA | 한국인터넷진흥원 표준 용어 |

### 내장 용어 사전
```
dictionary/security-terms-en-ko.json
```

## 번역 규칙

### 1. 번역하지 않는 항목

> **⛔ enum 값 번역 금지 (v2.5.0 가드레일 — 최우선):** 아래 13종 필드의 **값**은 등급/판정
> enum으로, `english_report`와 `korean_report` **양쪽 모두 영어 원문 그대로** 유지한다.
> korean_report에서도 절대 번역하지 않는다(표시 언어 처리는 HTML 템플릿 계층 책임).
>
> `severity` · `status` · `verdict` · `security_verdict` · `priority` · `confidence` ·
> `model_effectiveness` · `edge_type` · `component_type` · `target_type` · `pattern_type` ·
> `risk_level` · `gitignore_status`
>
> - 예: `"severity": "Critical"` → (KO에서도) `"Critical"` — `"심각"` 금지.
> - 예: `graph_verdict.security_verdict: "REMOVE"` → `"REMOVE"` — `"제거"` 금지.
> - 예: `recommendations[].priority: "High"` → `"High"` — `"높음"` 금지.
>
> **`compliance_tags`(V1.4)**: 불변 토큰. korean_report에 **byte-identical** 복사. 제어 항목명
> 한국어는 서술(prose)에서만(사전 `compliance_controls` 참조), 태그 문자열 치환 금지.

```
- 파일 경로: /path/to/file.js
- 코드 조각: eval("code")
- 패키지명: lodash, express
- CVE ID: CVE-2020-8203
- ID 필드: STATIC-001, VULN-001, REL-001, MODEL-001, REC-001
- recommendations 구조 필드: id, rank(정수 순서), finding_ids(배열) — 원형 유지
  ※ recommendations.priority는 enum — 번역 금지, 영어 원문 유지. action/rationale/category는 번역.
- code_fix 코드: code_fix.before, code_fix.after, code_fix.language — 코드/식별자는 원형 유지(번역 금지)
  ※ deep_dive_result(서술), code_fix.note(설명)는 번역 대상.
- compliance_tags: 불변 토큰 (byte-identical, 번역 금지)
- 라이선스명: MIT, Apache-2.0, GPL-3.0
- 기술 약어: SBOM, API, URL, JSON
- 모델 ID: claude-sonnet-4-6, claude-haiku-4-5-20251001 등
- severity 값: Critical, High, Medium, Low, Info (영어 원문 유지)
- status 값: Confirmed, Mitigated, False Positive 등 (영어 원문 유지)
- priority 값: Critical, High, Medium, Low (영어 원문 유지)
- verdict / security_verdict 값: INSTALL_OK, REVIEW, DISABLE, REMOVE (대문자 그대로 유지)
- model_effectiveness 값: VALID, DEGRADED, OBSOLETE, MODEL_LOCKED (대문자 그대로 유지)
- confidence / risk_level / gitignore_status 값: 영어 원문 유지
- edge_type 값: bundles, delegates_to, preloads, uses_mcp, invokes_hook, references
- component_type / target_type 값: 영어 원문 유지
- pattern_type 값: MC1, MC2, MC3, MC4, OB1
```

### 2. 번역하는 항목
```
- description: 상세 설명
- recommendation: 권장 조치
- issue: 이슈 제목
- risk_summary: 위험 요약
- rationale: 근거
- analysis: 분석 결과
- detail: 상세 내용
- deep_dive_result: 심층 분석 서술
```

> **⚠️ 완역 의무 (v2.5.1):** 위 서술 필드의 **부분 번역·생략은 실패로 간주**한다. 영문 문장이
> `korean_report`에 잔존하면 안 된다. 출력이 길면 카테고리별로 나눠서라도 **전량 번역**한다
> (Desktop 단일 컨텍스트에서 특히 주의 — 통째 출력하려다 서술을 빠뜨리지 말 것).

### 3. 용어 표준화

> **⚠️ 아래 Severity/Status 표는 서술 문장 안의 단어 번역용이다**(예: "이는 심각한 취약점입니다").
> **JSON enum 값(`severity`/`status` 필드)에는 적용하지 않는다** — enum 값은 §1 규칙대로 영어 원문 유지.

#### Severity 번역 (prose 전용)
| English | 한국어 |
|---------|--------|
| Critical | 심각 |
| High | 높음 |
| Medium | 중간 |
| Low | 낮음 |
| Info | 정보 |

#### Status 번역 (prose 전용)
| English | 한국어 |
|---------|--------|
| Confirmed | 확인됨 |
| Mitigated | 완화됨 |
| False Positive | 오탐 |
| Potential Risk | 잠재적 위험 |

#### 주요 용어 번역
| English | 한국어 |
|---------|--------|
| Vulnerability | 취약점 |
| Command Injection | 명령 주입 |
| Hardcoded Credential | 하드코딩된 자격 증명 |
| Sensitive Pattern | 민감 패턴 |
| Private Key | 개인키 |
| Access Token | 액세스 토큰 |
| Remote Code Execution | 원격 코드 실행 |
| Privilege Escalation | 권한 상승 |
| Prompt Injection | 프롬프트 인젝션 |
| Supply Chain Attack | 공급망 공격 |
| Typosquatting | 타이포스쿼팅 |
| Copyleft | 카피레프트 |
| License Incompatibility | 라이선스 비호환성 |
| Unpinned Version | 고정되지 않은 버전 |
| Deprecated Package | 지원 중단 패키지 |
| Relationship Graph | 연관관계 그래프 |
| Risk Propagation | 위험 전파 |
| Graph Verdict | 그래프 판정 |
| Model Validity | 모델 유효성 |
| Obsolescence | 진부화 |
| Model Effectiveness | 모델 효과성 |
| Retired Model | 은퇴 모델 |
| Hardcoded Model ID | 하드코딩된 모델 ID |
| Deprecated API Pattern | 폐기된 API 패턴 |
| Propagation Path | 전파 경로 |
| Component Type | 컴포넌트 타입 |
| Dangling Reference | 미해석 참조 |
| Chain-of-Thought Scaffolding | 연쇄적 사고 스캐폴딩 |

#### Verdict 번역 (값 자체는 영문 유지, 텍스트 설명만 번역)
| English (description) | 한국어 |
|---------|--------|
| "No significant risk; component may be installed" | "중요한 위험 없음; 설치 허용" |
| "Requires review before use" | "사용 전 검토 필요" |
| "Should be disabled until remediation" | "조치 완료 전 비활성화" |
| "Must be removed immediately" | "즉시 제거 필요" |
| "Operating as intended on current model" | "현행 모델에서 정상 동작" |
| "Partially works with reduced effectiveness" | "부분적으로 동작하나 효과 감소" |
| "Current model performs this natively" | "현행 모델이 네이티브로 수행" |
| "Locked to a retired or specific model" | "은퇴 또는 특정 모델에 고정됨" |

### 4. 문장 번역 패턴

#### 권장 조치 템플릿
```
영문: "Upgrade [package] to version [version] or later"
한글: "[package]를 [version] 이상 버전으로 업그레이드하세요"

영문: "Add [file] to .gitignore"
한글: "[file]을(를) .gitignore에 추가하세요"

영문: "Use environment variables instead of hardcoded values"
한글: "하드코딩된 값 대신 환경 변수를 사용하세요"

영문: "Implement input validation before processing"
한글: "처리 전 입력 검증을 구현하세요"

영문: "Replace with [alternative] for better security"
한글: "더 나은 보안을 위해 [alternative](으)로 교체하세요"
```

## 입력 형식

```json
{
  "english_report": {
    "repository_summary": { "graph_verdict": {} },
    "static_code_findings": [ ... ],
    "binary_analysis_findings": [ ... ],
    "skill_risk_findings": [ ... ],
    "agent_policy_findings": [ ... ],
    "sensitive_patterns": [ ... ],
    "prompt_optimization": [ ... ],
    "sbom_analysis": { ... },
    "relationship_findings": [ ... ],
    "model_validity_findings": [ ... ],
    "recommendations": [ ... ]
  }
}
```

## 출력 형식

```json
{
  "english_report": { ... },
  "korean_report": {
    "repository_summary": {
      "description": "프로젝트 설명",
      "file_statistics": { ... },
      "key_components": [ "컴포넌트 1", "컴포넌트 2" ],
      "sensitive_files_detected": [ "설명..." ]
    },
    "static_code_findings": [
      {
        "id": "STATIC-001",
        "file": "src/utils/shell.py",
        "line": 45,
        "issue": "명령 주입 위험",
        "description": "사용자 입력과 함께 os.system() 호출됨",
        "severity": "High",
        "status": "Confirmed",
        "deep_dive_result": "입력이 HTTP 요청에서 새니타이징 없이 전달됨",
        "recommendation": "shell=False로 subprocess를 사용하고 입력을 새니타이징하세요"
      }
    ],
    ...
  }
}
```

## 품질 보증

### 일관성 검증
1. 동일 용어는 동일하게 번역
2. 용어 사전 우선 적용
3. 컨텍스트 기반 번역

### 번역 불가 시
1. 영문 원문 유지
2. 괄호 안에 한글 설명 추가
   - 예: "Prototype Pollution (프로토타입 오염)"

### 번역 품질 체크리스트
- [ ] 모든 enum 값(severity·status·verdict·priority 등 13종)이 EN/KO 동일(영어 원문) — 번역 안 됨
- [ ] compliance_tags EN/KO byte-identical
- [ ] 기술 용어 표준화 (서술 문장 한정)
- [ ] 파일 경로/코드 미번역
- [ ] 문장 자연스러움
- [ ] 조사(은/는, 을/를) 적절성

## 확장 방법

### 새 언어 추가

1. 용어 사전 파일 생성
```
dictionary/security-terms-en-ja.json  # 일본어
dictionary/security-terms-en-zh.json  # 중국어
```

2. 번역 규칙 정의
```
dictionary/translation-rules-ja.md
```

3. 스킬 옵션에 언어 코드 추가
```
@bilingual-translator <report> --lang ja
```

### 사용자 정의 용어 추가

```json
{
  "custom_terms": [
    {
      "en": "Custom Term",
      "ko": "사용자 정의 용어"
    }
  ]
}
```

## 사용 예시

### 기본 사용
```
사용자: @bilingual-translator 다음 영문 보고서를 한글로 번역해줘
{
  "static_code_findings": [
    {
      "id": "STATIC-001",
      "issue": "Command Injection Risk",
      "description": "os.system() called with user input",
      "severity": "High",
      "recommendation": "Use subprocess with shell=False"
    }
  ]
}

응답:
{
  "english_report": { ... },
  "korean_report": {
    "static_code_findings": [
      {
        "id": "STATIC-001",
        "issue": "명령 주입 위험",
        "description": "사용자 입력과 함께 os.system() 호출됨",
        "severity": "High",
        "recommendation": "shell=False로 subprocess를 사용하세요"
      }
    ]
  }
}
```

### 다른 언어 (추후 지원)
```
@bilingual-translator <report> --lang ja
@bilingual-translator <report> --lang zh-CN
```

## 통합 워크플로우

```
[각 스캔 스킬] → 영문 결과 출력
        ↓
[report-merger] → 영문 보고서 통합
        ↓
[bilingual-translator] → 한글 보고서 생성
        ↓
최종 bilingual JSON 출력
```

## 제약 사항

1. **기계 번역 아님**: 용어 사전 기반 규칙 번역
2. **새 용어 처리**: 사전에 없는 용어는 영문 유지
3. **컨텍스트 한계**: 복잡한 문맥 파악 제한적
4. **실시간 사전 업데이트 불가**: 내장 사전 기반

## 버전 정보

- **Skill Version**: 1.0.0
- **Dictionary Version**: 1.0.0
- **지원 언어**: en, ko
