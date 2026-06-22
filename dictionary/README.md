# Security Terminology Dictionary

## Overview

보안, IT, 컴플라이언스 분야의 표준 용어 사전입니다. NIST, CIS, ISO 27001, OWASP 등 국제 표준을 참조하여 구성되었습니다.

## 파일 구성

| 파일 | 성격 |
|------|------|
| `security-terms-en-ko.json` | 보안 용어 영한 사전 |
| `translation-rules-ko.json` | 한글 번역 규칙·문장 패턴 |
| `model-capabilities.json` | 모델 능력/은퇴/진부화 레지스트리 (v2.1.0+) |
| `security-template.html` | **HTML 리포트 정식 템플릿(보안담당자용, source of truth)** — `@html-report-generator`가 JSON을 주입해 정적 HTML 리포트를 생성한다. `docs/index.html`은 이 파일을 가리키는 개발 미리보기 심링크. (v2.2.0+) |

## 참조 표준

| 표준 | 설명 | 출처 |
|------|------|------|
| NIST CSF 2.0 | Cybersecurity Framework | https://www.nist.gov/cyberframework |
| NIST Glossary | 10,000+ 보안 용어 | https://csrc.nist.gov/glossary |
| CIS Controls v8.1 | Critical Security Controls | https://www.cisecurity.org/controls |
| ISO 27001 | 정보보안 관리체계 | ISO/IEC 27001:2022 |
| OWASP | 웹 애플리케이션 보안 | https://owasp.org |
| KISA | 한국인터넷진흥원 용어 | https://www.kisa.or.kr |

---

## 용어 구조

```json
{
  "term_id": "TERM-001",
  "english": {
    "term": "Vulnerability",
    "definition": "Weakness in an information system...",
    "abbreviation": "VULN"
  },
  "korean": {
    "term": "취약점",
    "definition": "정보 시스템의 약점...",
    "abbreviation": null
  },
  "category": "security_finding",
  "source": "NIST SP 800-53",
  "related_terms": ["threat", "risk", "exposure"]
}
```

---

## 지원 언어

| 코드 | 언어 | 상태 |
|------|------|------|
| `en` | English | ✓ 지원 |
| `ko` | 한국어 | ✓ 지원 |
| `ja` | 日本語 | 예정 |
| `zh` | 中文 | 예정 |
| `es` | Español | 예정 |
| `de` | Deutsch | 예정 |

---

## 카테고리

1. **severity** - 심각도 관련
2. **finding_type** - 발견 유형
3. **security_control** - 보안 통제
4. **compliance** - 컴플라이언스
5. **vulnerability** - 취약점
6. **threat** - 위협
7. **risk** - 위험
8. **sbom** - 소프트웨어 구성표
9. **license** - 라이선스
10. **action** - 조치/권고
