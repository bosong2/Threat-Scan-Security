---
name: securityreports-help
description: "[DEPRECATED v2.3.0+] Security Reports 도움말. /threat-scan-help 를 사용하세요."
---

> ⚠️ **DEPRECATED (v2.3.0+)**: 이 명령은 구 SecurityScan 세대입니다.
> 신규 파이프라인 안내는 `/threat-scan-help`를 사용하세요.

# Security Reports - Help

Security Reports 보안 스캐너 명령어 목록입니다.

## 📌 사용 가능한 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/securityreports-scan` | 🔒 전체 보안 스캔 | `/securityreports-scan .` |
| `/securityreports-sbom` | 📦 의존성 보안 분석 | `/securityreports-sbom .` |
| `/securityreports-static` | 🔍 정적 코드 분석 | `/securityreports-static ./src` |
| `/securityreports-secrets` | 🔑 민감 정보 탐지 | `/securityreports-secrets .` |
| `/securityreports-help` | ❓ 도움말 (이 화면) | `/securityreports-help` |

## 🚀 빠른 시작

### GitHub 리포지토리 스캔
```
/securityreports-scan https://github.com/owner/repo
```

### 현재 프로젝트 스캔
```
/securityreports-scan .
```

### 특정 분석만 실행
```
/securityreports-sbom .          # 의존성만 분석
/securityreports-static ./src    # 소스 코드만 분석
/securityreports-secrets .       # 민감정보만 탐지
```

## 📊 출력 형식

모든 결과는 JSON 형식으로 출력됩니다:

```json
{
  "scan_metadata": {
    "scan_id": "SCAN-20260205-143022",
    "timestamp": "2026-02-05T14:30:22Z"
  },
  "findings_summary": {
    "total": 15,
    "by_severity": {
      "critical": 2,
      "high": 5,
      "medium": 6,
      "low": 2
    }
  },
  "english_report": { ... },
  "korean_report": { ... }
}
```

## 🎯 심각도 레벨

| 레벨 | 설명 | 조치 |
|------|------|------|
| Critical | 즉시 조치 필요 | 배포 중단 권고 |
| High | 빠른 조치 필요 | 1주 내 수정 |
| Medium | 계획된 수정 | 1달 내 수정 |
| Low | 개선 권장 | 백로그 등록 |
| Info | 정보성 알림 | 검토 |

## 📁 Finding ID 규칙

| 접두사 | 스캔 영역 |
|--------|-----------|
| STATIC-NNN | 정적 코드 분석 |
| SENS-NNN | 민감 정보 탐지 |
| VULN-NNN | 의존성 취약점 |
| LIC-NNN | 라이선스 이슈 |
| VER-NNN | 버전 이슈 |

## ℹ️ 추가 정보

- 스캔 대상 크기 제한: 100MB
- 지원 입력: 로컬 경로, GitHub URL, ZIP 파일
- 출력 언어: 영어 + 한글 (bilingual)
