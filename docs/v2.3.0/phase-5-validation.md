# Phase 5 — 검증

## 목표

Claude Code 동작·오케스트레이션·HTML 산출·Desktop 회귀·레거시 안내를 end-to-end로 검증한다.

## 검증 항목

| # | 항목 | 방법 | 기대 |
|---|------|------|------|
| 1 | 플러그인 로드 | `/plugin marketplace add <path>` → `install` → `/plugin` | `threat-scan-security` enabled, 충돌 없음 |
| 2 | 커맨드 노출 | Claude Code에서 `/threat-scan`, `/threat-scan-html`, `/threat-scan-help` | 3개 모두 인식 |
| 3 | 에이전트 노출 | `/agents` | `tss-*` 15개 표시 |
| 4 | 전체 스캔 E2E | `/threat-scan <샘플 경로>` | bilingual JSON + KO HTML 산출, 경로·verdict 보고 |
| 5 | 오케스트레이션 | 스캔 로그 | 오케스트레이터가 단계별 `tss-*` 에이전트 호출(중첩 없음) |
| 6 | 단계 경계 | 스캔 중 파일/셸 사용 | 단계 1–10 파일 생성 0건, 단계 0·11만 셸/파일 |
| 7 | HTML 단독 | `/threat-scan-html <json> ko` | python3 생성기로 HTML 산출, exit 0 |
| 8 | HTML 내용 | 산출 HTML 열기 | 헤더 EN/KO+프린트, KO 본문, 푸터 메타, 도넛 차트 |
| 9 | 스크립트 경로 | `CLAUDE_PLUGIN_ROOT` 설정 후 생성기 실행 | 플러그인 경로 템플릿 해석, repo/dist 회귀 없음 |
| 10 | **Desktop 회귀** | `bash build_claude_desktop.sh` | 성공, zip 구성 종전 동일, `VERSION=2.3.0` |
| 11 | 레거시 안내 | `/securityreports-scan` 또는 `/threat-scan-help` | DEPRECATED + `/threat-scan` 안내 노출 |

## 핵심 회귀 — Desktop 동등성

frontmatter 추가가 Desktop 빌드를 깨지 않는지 반드시 확인한다.

```bash
cd Threat-scan-security
out=$(bash build_claude_desktop.sh 2>&1)         # 파이프 truncation 회피: 전체 캡처
echo "$out" | grep "VERSION="                     # → VERSION=2.3.0
unzip -l threat-scan-security.zip | grep -E "security-template.html|generate_html_report.py|threat-scan-orchestrator|html-report-generator"
# 합성 SKILL.md에 frontmatter 잔재가 동작을 깨지 않는지(텍스트 포함은 허용) 육안 확인
```

- Desktop 산출물은 frontmatter를 본문 텍스트로 포함할 수 있으나, Desktop SKILL.md는 단일 프롬프트로 해석되므로 동작 비파괴. 깨짐이 확인되면 빌드 단계에서 frontmatter strip 로직 추가(범위 내 보정).

## 단일 원천 확인

```bash
# 에이전트가 분석 본문을 복제하지 않고 참조만 하는지
for f in agents/tss-*.md; do wc -l "$f"; done    # 각 thin(수십 줄 이내)
grep -L "CLAUDE_PLUGIN_ROOT\|skills/" agents/tss-*.md   # → 출력 없음(모두 참조)
```

## 완료 조건

- [ ] #1–#11 전부 통과.
- [ ] Desktop 빌드 회귀 없음(#10).
- [ ] 에이전트 본문이 SKILL.md 참조 형태(분석 본문 복제 0건).
- [ ] 단계 1–10 파일 생성 0건, 단계 0·11만 스크립트/파일(#6).
