# Claude Threat Scan V2.0 - Skills Index

## 개요

Claude Threat Scan V2.0은 AI 기반 리포지토리 보안 진단 도구로, 9개의 모듈화된 Skills와 1개의 Orchestrator로 구성됩니다.

---

## Skills 목록

### 1. Orchestrator 및 소스 처리

| Skill | 경로 | 설명 |
|-------|------|------|
| [threat-scan-orchestrator](../skills/threat-scan-orchestrator/SKILL.md) | `skills/threat-scan-orchestrator/` | 전체 스캔 프로세스 조율 및 최종 보고서 생성 |
| [source-handler](../skills/source-handler/SKILL.md) | `skills/source-handler/` | ZIP 해제, GitHub 클론, 샌드박스 관리 |

### 2. 스캔 Skills (Section 1-7)

| # | Skill | 경로 | 설명 |
|---|-------|------|------|
| 1 | [repo-indexer](../skills/repo-indexer/SKILL.md) | `skills/repo-indexer/` | 리포지토리 인덱싱 |
| 2 | [static-code-analyzer](../skills/static-code-analyzer/SKILL.md) | `skills/static-code-analyzer/` | 정적 코드 분석 |
| 3 | [binary-analyzer](../skills/binary-analyzer/SKILL.md) | `skills/binary-analyzer/` | 바이너리/컴파일 파일 분석 |
| 4 | [skill-security-analyzer](../skills/skill-security-analyzer/SKILL.md) | `skills/skill-security-analyzer/` | SKILL.md/도구 보안 분석 |
| 5 | [sensitive-pattern-matcher](../skills/sensitive-pattern-matcher/SKILL.md) | `skills/sensitive-pattern-matcher/` | 민감 패턴 매칭 |
| 6 | [agent-policy-verifier](../skills/agent-policy-verifier/SKILL.md) | `skills/agent-policy-verifier/` | 에이전트 정책 검증 |
| 7 | [prompt-optimizer](../skills/prompt-optimizer/SKILL.md) | `skills/prompt-optimizer/` | 프롬프트/포맷 최적화 |

### 3. SBOM Skills (Section 8-9, V2.0 신규)

| # | Skill | 경로 | 설명 |
|---|-------|------|------|
| 8 | [sbom-analyzer](../skills/sbom-analyzer/SKILL.md) | `skills/sbom-analyzer/` | SBOM 및 의존성 보안 분석 |

### 4. 보고서 생성 및 번역

| Skill | 경로 | 설명 |
|-------|------|------|
| [report-merger](../skills/report-merger/SKILL.md) | `skills/report-merger/` | 영문 보고서 병합 |
| [bilingual-translator](../skills/bilingual-translator/SKILL.md) | `skills/bilingual-translator/` | 한글 번역 및 bilingual JSON 생성 |

---

## 호출 방식

### 전체 스캔
```
@threat-scan-orchestrator <repository-path>
```

### 개별 스캔
```
@<skill-name> <repository-path>
```

---

## 관련 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| [Scanner 개발](./Scanner%20개발.md) | `docs/Scanner 개발.md` | 기능 명세 |
| [Prompt V2.0](./claude_threat_scan_prompt_v_2.md) | `docs/claude_threat_scan_prompt_v_2.md` | 프롬프트 정의 |
| [JSON Schema V1.2](./claude-threat-scan-json-schema-v1.2.md) | `docs/claude-threat-scan-json-schema-v1.2.md` | 출력 스키마 |
| [사용 가이드](./USAGE_GUIDE.md) | `docs/USAGE_GUIDE.md` | 사용 방법 |
| [용어 사전](../dictionary/README.md) | `dictionary/README.md` | 보안 용어 사전 |

---

## 버전 정보

| 항목 | 버전 |
|------|------|
| Skills | 2.0 |
| JSON Schema | 1.2 |
| Scanner | V2.0 |

---

## 디렉토리 구조

```
SecurityScan/
├── docs/
│   ├── Scanner 개발.md
│   ├── claude_threat_scan_prompt_v_2.md
│   ├── claude-threat-scan-json-schema-v1.2.md
│   ├── USAGE_GUIDE.md
├── dictionary/
│   ├── README.md
│   ├── security-terms-en-ko.json
│   └── translation-rules-ko.json
└── skills/
    ├── threat-scan-orchestrator/
    │   └── SKILL.md
    ├── source-handler/
    │   └── SKILL.md
    ├── repo-indexer/
    │   └── SKILL.md
    ├── static-code-analyzer/
    │   └── SKILL.md
    ├── binary-analyzer/
    │   └── SKILL.md
    ├── skill-security-analyzer/
    │   └── SKILL.md
    ├── sensitive-pattern-matcher/
    │   └── SKILL.md
    ├── agent-policy-verifier/
    │   └── SKILL.md
    ├── prompt-optimizer/
    │   └── SKILL.md
    ├── sbom-analyzer/
    │   └── SKILL.md
    ├── report-merger/
    │   └── SKILL.md
    └── bilingual-translato
    └── report-merger/
        └── SKILL.md
```
