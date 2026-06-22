---
description: Run a full Claude Threat Scan security audit and emit bilingual JSON + KO HTML report
argument-hint: <path-or-git-url-or-zip>
---

Run a full Claude Threat Scan security audit on: **$ARGUMENTS**

Use the `threat-scan-orchestrator` skill to drive the complete pipeline (단계 0–11):

- **단계 0** (`tss-source-handler`): 소스 준비 (local / ZIP / GitHub URL 자동 감지)
- **단계 1–8**: 정적 코드·바이너리·스킬 보안·연관관계 그래프·모델 유효성·민감 패턴·정책·프롬프트·SBOM 분석
- **단계 8.5** (`tss-deepdive`): Medium+ findings 심층 트리아지
- **단계 9–10**: 보고서 병합 + 한글 번역 → bilingual JSON
- **단계 11** (`tss-html-report`): 정적 KO HTML 리포트 생성

별도 요구가 없으면 **bilingual JSON 리포트와 KO HTML 리포트를 함께 산출**한다.
완료 시 산출 파일 경로(JSON·HTML)와 그래프 verdict 요약을 보고한다.
