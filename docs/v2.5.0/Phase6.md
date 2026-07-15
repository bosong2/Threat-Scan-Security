# Phase 6 — 버전 배선(2.5.0 / Schema V1.4) + E2E 검증 + Desktop 빌드 회귀

## 목표

전 Phase 산출물을 v2.5.0으로 배선하고, 픽스처 repo 풀스캔 E2E와 Desktop 빌드 회귀로
릴리스 품질을 확정한다.
근거: [issues/TS-2.5.0_PROMPT_compliance_tagging.md](issues/TS-2.5.0_PROMPT_compliance_tagging.md)
Phase 5–6.

**의존:** Phase 1–5 전부 완료.

## 6-A. 버전 배선

| 파일 | 변경 |
|------|------|
| `VERSION` | `2.5.0` |
| `.claude-plugin/plugin.json` | `"version": "2.5.0"` |
| `commands/threat-scan-help.md` | `(v2.5.0)` + 커맨드 표에 `/threat-scan-setup`(Phase 2에서 추가돼 있어야 함 — 확인) |
| `skills/report-merger/SKILL.md` | scanner_version 리터럴 `"Claude Threat Scan V2.5"` (2곳) |
| `skills/threat-scan-orchestrator/SKILL.md` | scanner_version 리터럴 `"V2.5"` (1곳) |
| `build_claude_desktop.sh` | Desktop description 버전 문자열 `v2.5.0` |
| `CHANGELOG.md` | v2.5.0 항목 신설 (아래) |

CHANGELOG v2.5.0 항목 구성:
- **Added**: Schema V1.4(`compliance_tags` — KISA 49·AILLM 9·TA 10) + CTID-D/V 통합,
  `validate_compliance_tags.py`, 사전 `compliance_controls`(59), HTML 태그 배지·`--coverage`,
  AI 구성요소 스캔범위 게이트(Phase 0(d)·`ai_agent_scope`), `/threat-scan-setup` 권한 사전등록,
  분석 에이전트 Glob/Grep, 다크 코드뷰+하이라이터.
- **Changed**: Monitor 정책 개정(OUTPUT_PATH 대기 한정 허용 — async Agent 실측 대응),
  번역기 ANTI-HANG·ITEM_RANGE·JSON-SAFETY, enum 번역 금지 가드레일(13종)+템플릿 canonEnum
  정규화, SBOM 서브헤딩 영어 고정, 권장 조치 섹션을 리포지토리 요약 직후로 재배치,
  verdict 4종 화이트리스트.
- **호환성 명시**: V1.4는 V1.3의 strict superset — `compliance_tags` 부재 = legacy로 유효.
  기존 리포트 렌더 하위호환(canonEnum).

## 6-B. 오케스트레이터 최종 배선 (`skills/threat-scan-orchestrator/SKILL.md`)

1. 단계 11(Phase 4 — HTML) 절에 **validator 선행 실행** 지시:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_compliance_tags.py" "<최종 scanreport JSON>"
   # exit 1 → 오류 카테고리 보고 후 중단(HTML 미생성). exit 2(warn-only) → 경고 요약 후 진행.
   ```
   (단계 11은 기존 셸 허용 단계 — 단계 1–10 추론 전용 경계 유지)
2. 스캔 순서 노트 1줄: "단계 1–8은 CTID-D로 태깅, 8.5는 CTID-V로 검증, 9–11은 태그 읽기전용."
   — Code·Desktop 양 섹션에 각각(Desktop 섹션은 서술형, BUG-02 준수).
3. 참조 표에 v1.4 스키마 문서 2종 + CTID 2종 추가(v1.3은 legacy 표기).

## 6-C. E2E 검증 — 픽스처 repo 풀스캔

**픽스처 repo 구성** (`/tmp` 등 임시 위치에 생성, repo에는 미포함):
- 하드코딩 시크릿 1건 (→ 기대: `#KISA-2_6` primary, MASKING CONTRACT 준수)
- eval-on-input 싱크 1건 (→ `#KISA-1_2`)
- `disallowed_tools` 없는 에이전트 YAML (→ `#AILLM-8_7`)
- Terraform public-ACL 버킷 (→ `#TA-T_I3`)
- 고의 오귀속 유도 finding 1건 (→ 8.5의 V-1 재귀속 발동 확인용)
- 양성 파일 1건
- `.claude/` 디렉터리 (→ Phase 0(d) 게이트 발동 확인용)

**`/threat-scan <픽스처>` 실행 후 확인 (권한 규칙 없는 프로젝트에서 시작):**
- [ ] Phase 0'' 권한 자동 셋업 — settings.local.json Write 승인 **정확히 1회** →
      규칙 병합 등록 확인. 동일 프로젝트 재실행 시 승인 0회.
- [ ] Phase 0(d) 게이트가 정확히 1회 질문(포함 선택) → `ai_agent_scope: "included"` 기록.
- [ ] 허용된 상호작용 2건(셋업 승인·게이트 질문) 외 사용자 개입 없이 Phase 5까지 완주.
- [ ] `validate_compliance_tags.py` exit 0.
- [ ] 태그가 CTID-D worked-example 기대와 일치(위 표).
- [ ] deep_dive_result에 V-rule 발동 흔적 ≥1 (재귀속 문장).
- [ ] korean_report의 `compliance_tags`가 english_report와 byte-identical.
- [ ] korean_report의 enum 값(severity 등 13종)이 전부 영문 — EN/KO enum diff 0.
- [ ] HTML: 태그 배지+tooltip, 전 섹션 enum 영문 통일, 권장 조치 위치, 다크 코드뷰,
      verdict 스타일 누락 0.

## 6-D. Desktop 빌드 회귀

```bash
bash build_claude_desktop.sh
```
- [ ] `grep -c "tss-" dist_claude_desktop/threat-scan-security/SKILL.md` = 0
- [ ] `grep -c "SCAN_TMP" .../SKILL.md` = 0 (Code 섹션 제거 회귀)
- [ ] `find dist_claude_desktop -name "*.sh" | wc -l` = 0
- [ ] Desktop 섹션(게이트 대화 질의·CTID 노트) 보존 확인
- [ ] 신규 자산 포함: `references/docs/`에 v1.4 문서 2종+CTID 2종,
      `references/scripts/validate_compliance_tags.py`, `references/dictionary/`에
      compliance_controls 포함 사전, 템플릿 신버전
- [ ] `grep -rn "V2\.4" dist_claude_desktop/.../SKILL.md` = 0 (changelog성 언급 제외)

## 6-E. 마무리

- [ ] `grep -rn '"Claude Threat Scan V2.4"' skills/ commands/ .claude-plugin/` = 0
      (docs 이력·CHANGELOG 제외).
- [ ] goal.md의 "이슈 → Phase 추적 표" 전 행이 구현됐는지 최종 대조.
- [ ] Phase별 커밋이 완료됐는지 확인 후 릴리스 커밋 + 태그 `v2.5.0`.
- [ ] **push는 사용자 승인 후** (`git push origin main && git push origin v2.5.0`).
