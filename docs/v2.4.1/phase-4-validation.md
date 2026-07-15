# Phase 4 — 통합 검증·회귀

## 목표

3종 수정이 happy 리포트에서 실제 해소되고, 뷰어 동기화·Desktop 빌드·버전 정합이 회귀 없이 유지됨을 확인한다.

## 검증 절차

### 4-A. 뷰어 동기화

```bash
diff docs/index.html dictionary/security-template.html   # 빈 출력이어야 함
```

### 4-B. happy 리포트 E2E 렌더

```bash
python3 scripts/generate_html_report.py \
  ~/Downloads/scanreport-20260624044705-happy.json --lang ko \
  --out /tmp/v241-happy.html
```

브라우저로 `/tmp/v241-happy.html` 열어 육안 확인:

- [ ] **①** 헤더 배지 `V2.4` 표시(`V2.1` 아님).
- [ ] **②** 리포지토리 요약: overview 설명 + 주요 우려사항 6건 + graph_verdict(DISABLE) 카드가 **데이터로 채워짐**.
- [ ] **③a** jsonwebtoken(CVE 4건) OSV 클릭 → 인라인 표시; CVE 다수 패키지에서 `+N 더보기` → 모달 + osv.dev 링크.
- [ ] **③b** 범위 스펙 패키지에서 concrete 버전 질의 + 캐비엇 배지.
- [ ] 브라우저 콘솔 JS 에러 0건.

### 4-C. 반응형

- [ ] 개발자도구 모바일 뷰(≤480px)에서 모달·요약 카드·테이블 레이아웃 정상.

### 4-D. 회귀 — 정본 스키마 리포트

- [ ] `description`/`key_components`/`file_statistics` 정본 필드 합성 JSON 렌더 시 요약 카드 정상(별칭 폴백이 정본을 가리지 않음).
- [ ] `scanner_version` 없는 JSON 렌더 시 배지 숨김/`-`, 깨짐 없음.

### 4-E. Desktop 빌드 회귀

```bash
bash build_claude_desktop.sh
unzip -l threat-scan-security.zip            # 구성 종전 동일
grep -c "tss-" dist_claude_desktop/threat-scan-security/SKILL.md   # 0
```

- [ ] 빌드 성공, zip 구성·경로 치환 회귀 없음.
- [ ] 템플릿(`references/...security-template.html`)에 수정분 반영 확인.

### 4-F. 버전 정합

```bash
cat VERSION                                  # 2.4.1
grep '"version"' .claude-plugin/plugin.json  # 2.4.1
grep -rn '"scanner_version"' skills/report-merger/SKILL.md skills/threat-scan-orchestrator/SKILL.md  # V2.4
```

### 4-G. CHANGELOG

- [ ] `CHANGELOG.md`에 v2.4.1 항목(3종 수정) 존재.

## 산출물

- 검증 통과 시 v2.4.1 커밋(사용자 승인 후). 커밋 메시지: `fix(report): v2.4.1 — version header + repo summary cards + OSV CVE modal/version-scope`.
- 실패 항목은 해당 Phase로 되돌려 수정 후 재검증.
