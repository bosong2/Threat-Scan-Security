# v2.2.0 — HTML 리포트 출력 스킬

## 목표 (1문장)

merge·번역(단계 9·10)이 끝난 bilingual JSON으로부터, 사람 개입·LLM 추론 없이 **보안담당자용 정적 HTML 리포트**를 결정론적으로 생성하는 스킬(`@html-report-generator`, 단계 11)을 추가한다.

## 배경

기존 파이프라인은 단계 10에서 **bilingual JSON만** 산출했다. HTML 리포트를 보려면 사람이 뷰어에 JSON을 올리고 "Export HTML"을 직접 눌러야 했다. 뷰어 `exportHTML()`은 본질적으로 "템플릿 + JSON 데이터블록 + boot script" 주입이라, 브라우저 없이 스크립트로 동일 결과를 재현할 수 있다 → 단계 11로 자동화한다.

## 불변 제약 (계승 + 신규)

1. **Schema V1.3 불변**: 입력 JSON을 변형하지 않고 그대로 임베드한다. (스키마 무관 동작)
2. **하위호환**: graph_verdict/recommendations 없는 v1.2 JSON도 오류 없이 렌더.
3. **결정론**: 동일 입력 → 동일 출력. 외부 네트워크·LLM 미사용, Python 표준 라이브러리만.
4. **단일 원천**: 템플릿은 `dictionary/security-template.html` 하나. `docs/index.html`은 이를 가리키는 개발 미리보기 심링크.
5. **(신규) 스크립트 실행 예외 단계**: 단계 0·11만 스크립트/파일 생성 허용. 단계 1–10은 종전대로 코드 실행·파일 생성 금지(Desktop 샌드박스 호환).

## 완료 정의 (Definition of Done)

- [x] `python3 scripts/generate_html_report.py <json> --lang ko` → `<json basename>.html` 생성, exit 0.
- [x] 산출 HTML에 export 스타일(`__tss_ex__`)·데이터블록(`__TSS__`)·boot script 주입, 데이터 내 `<`는 `<`로 이스케이프(리터럴 `</script>` 0건).
- [x] `--lang ko`→KO boot, `--lang en`→EN boot. 미존재 프로파일/입력은 명확한 에러+exit 1.
- [x] 데이터블록이 유효 JSON(`json.loads` 통과), EN/KO 모두 포함, `_filename` 제거.
- [x] `dictionary/security-template.html` 정식 원천화, `docs/index.html` 심링크.
- [x] 신규 스킬 `skills/html-report-generator/SKILL.md`, 오케스트레이터 단계 11 + 제약 carve-out.
- [x] `build_claude_desktop.sh`가 템플릿(.html)·스크립트(.py)·sub-skill 복사, zip 포함 확인.
- [x] dist 구조(`references/scripts` ↔ `references/dictionary`)에서 실행 시 repo 산출물과 동일.
- [x] `VERSION` = 2.2.0, 빌드 로그 `VERSION=2.2.0`.

## Phase 구성

| Phase | 문서 | 내용 |
|-------|------|------|
| 1 | `phase-1-template-canonicalize.md` | 템플릿 정식 원천화 + docs 심링크 |
| 2 | `phase-2-generator-script.md` | Python 생성기(exportHTML 1:1 재현·CLI·profile) |
| 3 | `phase-3-skill-and-orchestrator.md` | 신규 스킬 + 오케스트레이터 단계 11 + 제약 carve-out |
| 4 | `phase-4-build-packaging.md` | 빌드 템플릿/스크립트 복사 + VERSION |
| 5 | `phase-5-validation.md` | 동등성·EN/KO·하위호환·빌드·샌드박스 검증 |

## 범위 밖 (향후)

- IT 담당자용/일반 개발자용/고급 개발자용 템플릿 실제 제작(이번엔 `--profile` 골격 + security 템플릿만).
- 다국어(ja/zh) HTML, PDF 출력, 리포트 서명/암호화.
