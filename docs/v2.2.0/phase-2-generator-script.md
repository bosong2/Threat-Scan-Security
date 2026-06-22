# Phase 2 — HTML 리포트 생성기 스크립트

## 목표

뷰어 `exportHTML()`(security-template.html L1132–1186)을 브라우저·LLM 없이 1:1 재현하는 Python 3 스크립트 `scripts/generate_html_report.py`를 작성한다.

## 변환 사양 (exportHTML 재현)

base를 렌더된 DOM(`document.documentElement.outerHTML`)이 아니라 **RAW 템플릿 파일**로 삼는다 — boot script가 로드 시 재렌더하므로 결과 동일하고 사전 렌더 `#reportContent`가 없어 더 깔끔하다.

1. JSON 직렬화: `json.dumps(data, ensure_ascii=False, separators=(",",":"))` 후 `<` → `<`. (JS `JSON.stringify(...).replace(/</g,'\\u003C')` 동치. `JSON.parse`/`json.loads`가 복원)
2. `_filename` 키 제거.
3. 데이터블록: `<script id="__TSS__" type="application/json">\n{json}\n</script>`.
4. export 스타일: `<style id="__tss_ex__">#exportBtn,.upload-btn,.nav-controls{display:none!important}</style>`.
5. boot script(IIFE): `__TSS__` 파싱 → `_D._filename="<basename>"`, `currentLang="<lang>"`, `reports=[_D]`, lang-btn `.active` 동기화, `renderReport()`+`updateNav()`.
6. 주입 위치: 스타일=첫 `</head>` 앞, 데이터블록+boot=마지막 `</body>` 앞(`rfind`).

## CLI

```
python3 generate_html_report.py <report.json> [--lang ko|en]
    [--profile security] [--template <path>] [--out <path>]
```

- `--lang` 기본 `ko`. `--profile` 기본 `security`(→ `security-template.html`).
- `--template`이 `--profile`보다 우선. 미존재 프로파일/입력은 명확한 에러 + exit 1.
- `--out` 기본: 입력과 같은 디렉토리의 `<basename>.html`.
- 템플릿 탐색: repo(`scripts/../dictionary`)와 dist(`references/scripts/../dictionary`) 구조 모두 해석.

## 완료 조건 (검증 가능)

- [x] `py_compile` 통과, 표준 라이브러리만(`json`/`argparse`/`os`/`sys`).
- [x] KO/EN 각각 생성 성공, 데이터블록 `json.loads` 통과, EN/KO 모두 포함, `_filename` 제거.
- [x] 데이터 내 `<script>alert(1)</script>` 페이로드가 `<…`로 이스케이프(리터럴 `</script>` 0건).
- [x] 미존재 프로파일/입력 → 에러 메시지 + exit 1.

## 검증

```bash
python3 -m py_compile scripts/generate_html_report.py
python3 scripts/generate_html_report.py <sample>.json --lang ko
python3 scripts/generate_html_report.py <sample>.json --profile it-staff   # → exit 1
```
