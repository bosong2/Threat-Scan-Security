# Phase 1 — 템플릿 정식 원천화

## 목표

HTML 리포트 템플릿의 단일 원천(source of truth)을 `dictionary/security-template.html`로 확정하고, `docs/index.html`은 이를 가리키는 개발 미리보기 심링크로 강등한다. (드리프트 제거)

## 변경

1. 현 `docs/index.html`(뷰어 전체) → `dictionary/security-template.html`로 이관(정식 원천).
2. `docs/index.html` → `../dictionary/security-template.html` 상대 심볼릭 링크.
3. `dictionary/README.md`에 파일 구성표 추가(JSON 사전 3종 + `security-template.html`).

### 심링크 불가 환경 대비

심링크를 지원하지 않는 체크아웃 환경에서는 `docs/index.html`을 `dictionary/security-template.html`의 복사본으로 두고 수동 동기화한다. 빌드(`build_claude_desktop.sh`)는 항상 `dictionary/security-template.html`(실파일)을 복사하므로 심링크 여부와 무관하다.

## 완료 조건 (검증 가능)

- [x] `dictionary/security-template.html` 존재(약 80KB, 뷰어 전체).
- [x] `docs/index.html`이 심링크이며 타깃이 `../dictionary/security-template.html`.
- [x] 심링크를 통해 파일 읽기 정상(`test -f docs/index.html` 성공, 1308 lines).
- [x] `dictionary/README.md` 파일 구성표에 템플릿 항목 존재.

## 검증

```bash
ls -la docs/index.html                       # → 심링크 표시
test -f docs/index.html && wc -l docs/index.html
grep -q security-template.html dictionary/README.md && echo OK
```
