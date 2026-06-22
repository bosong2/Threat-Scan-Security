---
description: Generate a static HTML report from an existing Claude Threat Scan JSON report
argument-hint: <report.json> [ko|en]
---

기존 bilingual JSON 리포트로부터 정적 HTML 리포트를 생성한다: **$ARGUMENTS**

1. 인자에서 JSON 경로와 언어(`ko` 또는 `en`, 기본 `ko`)를 파싱한다.
2. `tss-html-report` 에이전트를 호출하거나, 직접 Bash로 실행:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate_html_report.py" \
     "<report.json>" --lang <ko|en>
   ```
   (env 미설정 시 repo의 `scripts/generate_html_report.py`)
3. 산출 HTML 경로를 보고한다.

LLM 추론 없이 결정론적 파일 처리. 전체 재스캔 없이 HTML만 재생성할 때 사용한다.
