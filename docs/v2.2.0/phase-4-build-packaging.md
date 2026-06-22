# Phase 4 — 빌드·패키징·버전

## 목표

`build_claude_desktop.sh`가 HTML 템플릿과 생성기 스크립트를 dist에 포함하도록 확장하고, 버전을 2.2.0으로 올린다.

## 변경 — `build_claude_desktop.sh`

1. `SCRIPTS_DIR="${REF_DIR}/scripts"` 변수 + `mkdir -p`.
2. Dictionary 복사 루프에 `*.html` 추가(기존 `*.json`만) → `security-template.html`이 `references/dictionary/`로.
3. Scripts 복사 단계 신설: `scripts/*.py` → `references/scripts/`.
4. 메인 SKILL.md 생성 시:
   - Sub-Skill 참조표에 `HTML Report Generator | references/sub-skills/html-report-generator.md` 행.
   - "HTML 리포트 생성 참조(단계 11)" 섹션: 스크립트·템플릿 경로 + 실행 예시.
   - description 문구: v2.1.1 → v2.2.0, "정적 HTML 리포트" 추가.
5. `html-report-generator/SKILL.md`는 기존 sub-skill 복사 루프가 자동 처리(오케스트레이터만 제외).

## 변경 — `VERSION`

- `2.1.1` → `2.2.0`.

## 완료 조건 (검증 가능)

- [x] `bash build_claude_desktop.sh` 성공, 로그 `VERSION=2.2.0`.
- [x] zip 내 `references/dictionary/security-template.html` 존재.
- [x] zip 내 `references/scripts/generate_html_report.py` 존재.
- [x] zip 내 `references/sub-skills/html-report-generator.md` 존재.
- [x] dist 구조에서 생성기 실행 시 repo 산출물과 byte-identical.

## 검증

```bash
bash build_claude_desktop.sh | grep "VERSION="
unzip -l threat-scan-security.zip | grep -E "security-template.html|generate_html_report.py|html-report-generator.md"
```
