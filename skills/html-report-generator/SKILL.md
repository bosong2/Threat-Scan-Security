---
name: html-report-generator
description: >
  Generate a static HTML security report from a bilingual JSON scan report
  using the bundled Python generator script. Deterministic, no LLM reasoning.
---

# HTML Report Generator Skill

## 개요

병합·번역이 완료된 bilingual JSON 스캔 리포트를 입력받아 **보안담당자용 정적 HTML 리포트**를 생성하는 스크립트 기반 스킬(v2.2.0+).

뷰어 템플릿(`dictionary/security-template.html`)에 JSON 데이터블록과 boot script를 주입하여, 브라우저에서 열면 헤더(EN/KO 토글·프린트만), 푸터(리포트/스키마 버전·Author·Org·스캐너 모델·생성일), 위험 분포 도넛 차트, 권장조치 추적성까지 자동 구성된 자기완결 HTML을 만든다.

**LLM 추론을 사용하지 않는다.** 결정론적 파일 처리(템플릿 + JSON → HTML)이며 번들된 Python 스크립트로 수행한다. Claude Desktop 샌드박스에서는 이 번들 스크립트를 코드 실행 환경에서 돌려 다운로드용 HTML을 생성한다(단계 0 `source-handler`처럼 스크립트 실행이 허용되는 예외 단계).

## 역할

1. bilingual JSON 리포트 수신 (단계 9·10 산출물)
2. 프로파일에 해당하는 HTML 템플릿 로드 (기본: 보안담당자용 `security-template.html`)
3. JSON 데이터블록 + 언어 설정 boot script 주입
4. 정적 HTML 리포트 파일 출력

## 호출 방법

```
python3 references/scripts/generate_html_report.py <report.json> [옵션]
```

(repo 개발 환경에서는 `scripts/generate_html_report.py`)

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--lang` | 표시 언어 `ko` \| `en` | `ko` |
| `--profile` | 템플릿 프로파일 | `security` |
| `--template` | 템플릿 파일 직접 지정 (`--profile` 무시) | (프로파일 매핑) |
| `--out` | 출력 HTML 경로 | 입력과 같은 디렉토리의 `<basename>.html` |

### 프로파일 (템플릿 매핑)

| 프로파일 | 템플릿 | 대상 | 상태 |
|----------|--------|------|------|
| `security` | `security-template.html` | 보안 담당자 | ✓ 지원 |
| `it-staff` | (예정) | IT 운영 담당자 | 예정 |
| `dev` | (예정) | 일반 개발자 | 예정 |
| `advanced` | (예정) | 고급 개발자 | 예정 |

## 입력 형식

단계 9(`@report-merger`)·10(`@bilingual-translator`)가 산출한 **Schema V1.3 bilingual JSON** (`scan_metadata` + `english_report` + `korean_report`). 스키마 버전·필드 유무에 무관하게 동작한다(렌더는 템플릿 JS가 graceful 처리). v1.2 페이로드도 그대로 지원.

## 출력 형식

- 단일 정적 HTML 파일. 외부 의존성은 Chart.js CDN(SRI 포함, 오프라인 시 SVG 폴백)뿐.
- 파일명: 기본 `<입력 JSON basename>.html` (예: `scanreport-20260622143000.json` → `scanreport-20260622143000.html`).
- `--lang ko`면 KO 버튼 활성·한글 본문, `--lang en`이면 EN 버튼 활성·영문 본문으로 열린다.

## 워크플로우

```
[단계 9·10] → bilingual JSON 산출
        ↓
[html-report-generator] → 스크립트 실행 (LLM 미사용)
        ↓
JSON + (기본) KO HTML 리포트 출력
```

오케스트레이터는 **별도 요구가 없으면 JSON과 KO HTML을 함께** 출력한다. 사용자가 언어/프로파일을 지정하면 해당 옵션으로 생성한다.

## 동작 원리 (exportHTML 1:1 재현)

뷰어의 "Export HTML" 버튼(`exportHTML()`)과 동일한 변환을 스크립트로 재현한다:

1. 템플릿 HTML 읽기 (RAW 파일 — 렌더된 DOM 아님).
2. JSON 직렬화 후 `<` → `<` 치환 (HTML 파서가 데이터 내부 `</script>`를 못 보게; `JSON.parse`가 복원).
3. `<script id="__TSS__" type="application/json">…</script>` 데이터블록 구성.
4. `<style id="__tss_ex__">#exportBtn,.upload-btn,.nav-controls{display:none!important}</style>` 주입 → 헤더에서 EN/KO·프린트만 노출.
5. boot script(IIFE): 데이터 파싱 → `currentLang` 설정 → `reports=[…]` → lang-btn 동기화 → `renderReport()`.
6. 스타일은 첫 `</head>` 앞, 데이터블록+boot는 마지막 `</body>` 앞에 주입.

## 제약 사항

- **스크립트 실행이 허용되는 예외 단계**(단계 0·11). 단계 1–10의 "코드 실행 금지" 제약과 별개.
- 템플릿은 `dictionary/security-template.html`이 **단일 원천**. `docs/index.html`은 이를 가리키는 개발 미리보기 심링크.
- LLM 추론 미사용 — 입력 JSON을 변형하지 않고 그대로 임베드한다.
- 표준 라이브러리만 사용(Python 3), 외부 네트워크·의존성 없음, 동일 입력 → 동일 출력.

## 버전 정보

- **Skill Version**: 1.0.0 (v2.2.0 도입)
- **Template (security)**: `dictionary/security-template.html`
- **지원 언어**: ko, en
