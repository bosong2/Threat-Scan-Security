# Phase 4 — 스킬·에이전트 계층 일괄 개정 (CTID-D/V 통합 + patch2 가드레일)

## 목표

파이프라인의 **생성·검증·병합·번역 스킬**(양 모드 공유 단일 원천)에 ① Compliance Tagging
디렉티브(CTID-D/V)와 ② patch2의 enum 번역 금지·verdict 화이트리스트 가드레일을 일괄 반영한다.
근거: [issues/compliance-tagmap-distilled.md](issues/compliance-tagmap-distilled.md)(CTID-D),
[issues/compliance-tagging-deepdive.md](issues/compliance-tagging-deepdive.md)(CTID-V),
[issues/TS-2.5.0_patch2.md](issues/TS-2.5.0_patch2.md) §3.1–3.4.

**의존:** Phase 3 완료(참조할 v1.4 문서·CTID 정식 배치가 존재해야 함).

## 4-A. CTID-D 태깅 블록 — emitting 스킬 8개

**대상:** `skills/static-code-analyzer/SKILL.md`, `skills/binary-analyzer/SKILL.md`,
`skills/skill-security-analyzer/SKILL.md`, `skills/sensitive-pattern-matcher/SKILL.md`,
`skills/agent-policy-verifier/SKILL.md`, `skills/securityreports-sbom/SKILL.md`,
`skills/relationship-graph-analyzer/SKILL.md`, `skills/model-validity-analyzer/SKILL.md`

각 스킬에 **균일한 태깅 블록 정확히 1개**를 추가(최소 diff, 기존 구조 재편 금지):

```markdown
## Compliance Tagging (v2.5.0 — Schema V1.4)

finding 생성 시점에 `compliance_tags`를 부여한다. 규칙은
`${CLAUDE_PLUGIN_ROOT}/docs/compliance-tagmap-distilled.md`(CTID-D)를 로드해 따른다
(env 미설정 시 repo `docs/` 경로).

- 문법: `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$` · 0–4개 유일 · primary(근본원인) 우선.
- 근본원인 기준 태깅(증상 아님). 해당 제어 없으면 `[]`. 근사 태깅 금지.
- CWE/OWASP-LLM/ATLAS 식별자는 prose(description/recommendation) 전용 — `#`-태그 금지.
- 이 단계의 기대 범위: <CTID-D §2 해당 행 삽입>
```

단계별 기대 범위 행(CTID-D §2에서 발췌 — 각 스킬에 자기 행만):

| 스킬 | 기대 범위 |
|------|-----------|
| static-code-analyzer | `#KISA-1_*`–`#KISA-7_*`, `#AILLM-*`(LLM 코드 경로), `#TA-*`(IaC 파일) |
| binary-analyzer | `#KISA-2_15`, `#KISA-6_2`, `#KISA-7_2` |
| skill-security-analyzer | `#KISA-1_*`, `#AILLM-8_1`–`8_4`, `8_7` |
| sensitive-pattern-matcher | `#KISA-2_5`, `2_6`, `2_12`, `2_13`, `#AILLM-8_4` |
| agent-policy-verifier | `#AILLM-8_1`, `8_2`, `8_5`, `8_6`, `8_7` |
| securityreports-sbom | `#KISA-7_2`, `#KISA-2_15`, `#AILLM-8_9`, `#TA-A_B1` |
| relationship-graph-analyzer | `[]` 기본; 해당 시 `#KISA-7_2` |
| model-validity-analyzer | `[]` 기본; deprecated 모델/API에 `#KISA-7_2` |

추가 규칙(블록 내): `AILLM`은 LLM/에이전트 기능 확인 시에만, `TA`는 IaC/설정 아티팩트 증거
시에만. 태그는 분류 메타데이터 — MASKING CONTRACT 등 기존 증거 마스킹 규칙을 완화하지 않음.

**금지:** `prompt-optimizer`·`repo-indexer` 스킬에는 태깅 블록을 추가하지 않는다
(prompt_optimization·repository_summary는 태깅 금지 위치).

## 4-B. Deep-dive 태그 검증 (`skills/securityreports-deepdive/SKILL.md`)

"Tag Verification" 절 신설 — CTID-V(`docs/compliance-tagging-deepdive.md`) 참조 지시 + 요지 폴딩:

1. 기존 Level 1–3 절차에 태그 태스크 폴딩(별도 pass 아님):
   L1=primary 태그의 근본원인 트리거 대조, L2=재귀속(re-attribution) 탐지, L3=보조 태그 추가(≤4)·순서 확정.
2. V-1~V-7 규칙 수록: 재귀속 시 `deep_dive_result`에 1문장 기록(V-1), status와 태그 독립
   (Mitigated/False Positive여도 태그 유지, V-2), 증거 확장 금지(V-6), write-back 시 형식
   재검증(V-7 — 8.5가 병합 전 마지막 추론 단계).
3. 세션당 1회 cross-finding sweep 3종: 동일 결함 태그 일관성 / 배열별 범위 타당성 /
   AILLM 게이트 정합(리포지토리에 LLM 기능 실재 확인).
4. `code_fix` 자기일관성 게이트: fix는 primary 태그의 제어를 교정해야 함 — 불일치 시 해소 후 write-back.
5. 출력 계약 delta: `compliance_tags` in-place 검증·수정(빈 배열화 가능 — V-5),
   태그 변경 시에만 `deep_dive_result`에 사유 1문장. 그 외 필드 추가 없음.

## 4-C. 병합 스킬 (`skills/report-merger/SKILL.md`)

1. **태그 패스스루 규칙**: `compliance_tags`는 verbatim 통과. finding 내 dedup만 허용,
   재정렬 금지(primary-first는 의미론), finding 간 dedup/재배치 금지.
2. **patch2 verdict 화이트리스트**: 모든 finding.verdict ∈ {INSTALL_OK, REVIEW, DISABLE, REMOVE}.
   비정본 값(`MASK`·`KEEP` 등) 수신 시 → `REVIEW`로 정규화하고 원값 의미를 recommendation에 보존.
3. 체크리스트에 추가: 태그 금지 변형(`tags`·`control_mapping` 등) 필드 발견 시 `compliance_tags`로
   정규화 금지 — 스키마 위반으로 보고(발명 필드는 생성 단계 버그).

## 4-D. 번역 스킬 (`skills/bilingual-translator/SKILL.md`) — patch2 §3.1 + 태그 불변

1. **"번역 금지 — 구조·등급 enum 값" 통합 규칙 신설** (patch2 §3.1 명세 그대로):
   severity·status·verdict·security_verdict·priority·confidence·model_effectiveness·
   edge_type·component_type·target_type·pattern_type·risk_level·gitignore_status 값은
   EN/KO 모두 영어 원문. 표시 언어 처리는 템플릿 계층 책임.
2. **모순 지침 동반 개정** (반드시 함께 — 현행 행 번호는 v2.4.1 기준):
   - :72 "priority는 등급 번역(Critical→심각)" → "priority는 enum — 번역 금지".
   - :78 verdict 규칙 → 통합 규칙으로 흡수(`security_verdict` 포함 명시).
   - :100 용어 표 `Critical→심각` → "서술 문장 내 번역용, JSON enum 값 비적용" 주석.
   - :217·:306 예시 `"severity": "높음"` → `"severity": "High"`.
   - :241 체크리스트 "모든 severity 값 일관되게 번역" → "모든 enum 값 EN/KO 동일(영문) 확인".
3. **`compliance_tags` 불변 토큰**: korean_report에 byte-identical 복사. 제어 항목명
   한국어는 prose에서만(사전 `compliance_controls` 참조), 태그 문자열 치환 금지.

## 4-E. 민감 패턴 스킬 (`skills/sensitive-pattern-matcher/SKILL.md`) — patch2 §3.4

- verdict 필드(§ 출력 스키마, 현행 :110 부근): "**INSTALL_OK / REVIEW / DISABLE / REMOVE 4종만
  허용**. `MASK`·`KEEP` 등 임의 값 발명 금지. '마스킹 필요' 의미는 verdict가 아니라
  `recommendation` 텍스트로 서술."

## 4-F. Code 에이전트 1줄 반영 (`agents/tss-*.md`)

방법론 비복제 원칙 유지 — Rules에 요지 1줄씩만:

- emitting 8개 대응 에이전트(`tss-static-analyzer` 등): "compliance_tags 부여 — SKILL.md의
  Compliance Tagging 절 준수(문법·0–4·primary-first)."
- `tss-deepdive`: "태그 검증 포함 — CTID-V(V-1~V-7)." 
- `tss-report-merger`: "태그 verbatim 패스스루·verdict 4종 화이트리스트."
- `tss-translator`: "enum·compliance_tags 번역 금지(영문 원문 유지)."

## 완료 조건 (검증 가능)

- [ ] `grep -l "Compliance Tagging" skills/*/SKILL.md | wc -l` = 8 (emitting 8개 정확히 —
      prompt-optimizer·repo-indexer 미포함).
- [ ] 각 emitting 스킬에 태깅 블록 정확히 1개 + 자기 단계의 기대 범위 행.
- [ ] deepdive 스킬에 Tag Verification 절 + CTID-V 참조 + V-1~V-7 + 3 sweep.
- [ ] `grep -rn "등급 번역" skills/ docs/SCHEMA_V1.4_ENFORCEMENT.md` = 0건
      (v1.3 enforcement 원본 제외 — legacy 보존).
- [ ] bilingual-translator에 `"severity": "높음"` 예시 0건, enum 통합 규칙 존재.
- [ ] sensitive-pattern-matcher·report-merger에 verdict 화이트리스트 존재.
- [ ] recommendations·prompt_optimization 태깅 지시가 어느 스킬에도 없음.
