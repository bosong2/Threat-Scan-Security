# Phase 5 — 검증

## 목표

생성기·빌드·뷰어 동등성을 end-to-end로 검증한다.

## 검증 항목 및 결과

| # | 항목 | 방법 | 결과 |
|---|------|------|------|
| 1 | 스크립트 단독 | `generate_html_report.py <json> --lang ko` | ✅ `.html` 생성, exit 0 |
| 2 | 주입 정확성 | grep `__tss_ex__`/`__TSS__`/`currentLang="ko"`/`<` | ✅ 모두 주입, `<` 이스케이프 |
| 3 | 데이터블록 유효성 | 추출 후 `json.loads` | ✅ 파싱 통과, EN/KO 포함, `_filename` 제거, 리터럴 `</script>` 0건 |
| 4 | 언어 분기 | `--lang en` | ✅ `currentLang="en"` boot |
| 5 | 프로파일 골격 | `--profile security` / `--profile it-staff` | ✅ 정상 / 명확한 에러 + exit 1 |
| 6 | 입력 에러 | 미존재 JSON | ✅ 에러 + exit 1 |
| 7 | 빌드 | `bash build_claude_desktop.sh` | ✅ 성공, `VERSION=2.2.0`, 120K |
| 8 | 패키징 | `unzip -l` | ✅ template/script/sub-skill 포함 |
| 9 | dist 경로 해석 | dist 스크립트로 생성 | ✅ repo 산출물과 byte-identical |
| 10 | 하위호환 | 생성기는 스키마 무관 임베드(JSON 무변형) | ✅ v1.2 JSON도 그대로 임베드, 렌더는 템플릿 JS가 graceful |

## 뷰어 렌더 동등성 (수동 확인 항목)

스크립트 산출 HTML은 뷰어 `exportHTML()`과 **동일한 주입 사양**(스타일/데이터블록/boot)을 따르므로, 브라우저에서 열면 다음이 자동 구성된다(수동 육안 확인):

- 헤더: EN/KO 토글 + 프린트 버튼만(Export/Load/Nav 숨김 — `__tss_ex__` 스타일).
- 푸터: 리포트/스키마 버전·Author(Bosung Hong)·Org(Security Dept.)·스캐너 모델·생성일(`renderFooter`).
- 본문: `--lang ko`면 KO 버튼 활성·한글, `--lang en`면 EN·영문.
- 위험 분포 도넛 차트(Chart.js, 오프라인 시 SVG 폴백), 종합 위험도, 권장조치 추적성 칩.

## Desktop 샌드박스 (가정 검증)

번들 Python 스크립트(`references/scripts/generate_html_report.py`)는 Desktop 스킬 코드 실행 샌드박스에서 `references/dictionary/security-template.html`을 읽어 다운로드용 HTML을 생성한다. dist 경로 해석이 정상 동작함을 #9에서 확인.
