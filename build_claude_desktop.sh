#!/bin/bash
# ============================================================
# Claude Desktop 스킬 배포 패키지 빌드 스크립트
# 
# 사용법: bash build_claude_desktop.sh
# 결과물: threat-scan-security.zip
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist_claude_desktop"
SKILL_DIR="${DIST_DIR}/threat-scan-security"
REF_DIR="${SKILL_DIR}/references"
SUB_SKILLS_DIR="${REF_DIR}/sub-skills"
DICT_DIR="${REF_DIR}/dictionary"
DOCS_DIR="${REF_DIR}/docs"
SCRIPTS_DIR="${REF_DIR}/scripts"
ZIP_FILE="${SCRIPT_DIR}/threat-scan-security.zip"

VERSION=$(cat "${SCRIPT_DIR}/VERSION" 2>/dev/null || echo "unknown")
echo "🔧 Claude Desktop 스킬 배포 패키지 빌드 시작... (VERSION=${VERSION})"
echo ""

# 1. 기존 배포 디렉토리 정리
if [ -d "$DIST_DIR" ]; then
    rm -rf "$DIST_DIR"
fi
if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
fi

# 2. 디렉토리 구조 생성
mkdir -p "$SUB_SKILLS_DIR"
mkdir -p "$DICT_DIR"
mkdir -p "$DOCS_DIR"
mkdir -p "$SCRIPTS_DIR"

echo "📁 디렉토리 구조 생성 완료"

# 3. 메인 SKILL.md 생성
echo "📝 통합 SKILL.md 생성 중..."

# 오케스트레이터 본문만 추출 — 선행 YAML frontmatter(--- ... ---) 제거.
# (frontmatter의 Claude Code 전용 allowed-tools: Agent(tss-*) 가 Desktop SKILL.md에
#  섞이지 않도록 함. dual-mode 회귀 방지)
ORCH_BODY=$(awk 'BEGIN{fm=0} NR==1 && $0=="---"{fm=1; next} fm==1 && $0=="---"{fm=2; next} fm!=1{print}' "${SCRIPT_DIR}/skills/threat-scan-orchestrator/SKILL.md")

cat > "${SKILL_DIR}/SKILL.md" << 'SKILLEOF'
---
name: threat-scan-security
description: >
  AI 기반 보안 위협 스캐너 v2.3.1. 코드 리포지토리, ZIP 파일, GitHub URL을 대상으로
  정적 코드 분석, 바이너리 분석, 민감 정보 탐지, SBOM 의존성 분석(17개 생태계·lock 파일 인식), 에이전트 정책 검증,
  스킬 보안 분석, 컴포넌트 연관관계 그래프 분석, 모델 유효성/진부화 판정을 수행하고
  영문/한글 bilingual JSON 보고서와 정적 HTML 리포트를 생성합니다.
  "보안 스캔", "security scan", "threat scan", "코드 분석", "취약점 분석" 요청 시 사용됩니다.
---

SKILLEOF

# 오케스트레이터 본문 추가
echo "$ORCH_BODY" >> "${SKILL_DIR}/SKILL.md"

# sub-skill 참조 안내 섹션 추가
cat >> "${SKILL_DIR}/SKILL.md" << 'APPENDEOF'

---

## Sub-Skill 참조

각 분석 단계에서 아래 참조 파일의 지시문을 읽고 따릅니다:

| 모듈 | 참조 파일 |
|------|-----------|
| Source Handler | `references/sub-skills/source-handler.md` |
| Repository Indexer | `references/sub-skills/repo-indexer.md` |
| Static Code Analyzer | `references/sub-skills/static-code-analyzer.md` |
| Binary Analyzer | `references/sub-skills/binary-analyzer.md` |
| Skill Security Analyzer | `references/sub-skills/skill-security-analyzer.md` |
| Relationship Graph Analyzer | `references/sub-skills/relationship-graph-analyzer.md` |
| Model Validity Analyzer | `references/sub-skills/model-validity-analyzer.md` |
| Sensitive Pattern Matcher | `references/sub-skills/sensitive-pattern-matcher.md` |
| Agent Policy Verifier | `references/sub-skills/agent-policy-verifier.md` |
| Prompt Optimizer | `references/sub-skills/prompt-optimizer.md` |
| SBOM Analyzer | `references/sub-skills/securityreports-sbom.md` |
| Deep Dive Analyzer | `references/sub-skills/securityreports-deepdive.md` |
| Report Merger | `references/sub-skills/report-merger.md` |
| Bilingual Translator | `references/sub-skills/bilingual-translator.md` |
| HTML Report Generator | `references/sub-skills/html-report-generator.md` |

## 스키마 및 문서 참조

보고서 생성 시 다음 스키마/문서 파일을 참조합니다:
- `references/docs/SCHEMA_V1.3_ENFORCEMENT.md` — Schema V1.3 엄격 준수 규칙 (v1.2 포함)
- `references/docs/claude-threat-scan-json-schema-v1.3.md` — JSON Schema V1.3 정의
- `references/docs/SCHEMA_V1.2_ENFORCEMENT.md` — Schema V1.2 엄격 준수 규칙 (하위 호환 참조)
- `references/docs/claude-threat-scan-json-schema-v1.2.md` — JSON Schema V1.2 정의 (하위 호환 참조)
- `references/docs/claude_threat_scan_prompt_v_2.md` — Threat Scan 프롬프트 V2

## 번역 참조

한글 보고서 생성 시 다음 파일을 참조합니다:
- `references/dictionary/security-terms-en-ko.json` — 보안 용어 영한 사전 (verdict/model_effectiveness 포함)
- `references/dictionary/translation-rules-ko.json` — 한글 번역 규칙
- `references/dictionary/model-capabilities.json` — 모델 능력 레지스트리 (v2.1.0+)

## HTML 리포트 생성 참조 (단계 11, v2.2.0+)

bilingual JSON 산출 후 HTML 리포트 생성 시 다음 파일을 사용합니다:
- `references/scripts/generate_html_report.py` — HTML 리포트 생성기 (LLM 미사용, 결정론적)
- `references/dictionary/security-template.html` — 보안담당자용 HTML 템플릿 (기본 프로파일)

실행: `python3 references/scripts/generate_html_report.py <report.json> --lang ko`
(별도 요구가 없으면 JSON과 KO HTML을 함께 출력)

---

## 저작자 · 라이선스

- **Author**: Bosung Hong (bosong2)
- **License**: Apache-2.0 (`LICENSE`, `NOTICE` 참조)
- **Repository**: https://github.com/bosong2/Threat-Scan-Security
APPENDEOF

echo "✅ SKILL.md 생성 완료"

# 4. Sub-skill 파일 복사
echo "📋 Sub-skill 파일 복사 중..."
for skill_dir in "${SCRIPT_DIR}/skills"/*/; do
    skill_name=$(basename "$skill_dir")
    # 오케스트레이터는 메인 SKILL.md에 이미 포함되므로 건너뜀
    if [ "$skill_name" = "threat-scan-orchestrator" ]; then
        continue
    fi
    if [ -f "${skill_dir}SKILL.md" ]; then
        cp "${skill_dir}SKILL.md" "${SUB_SKILLS_DIR}/${skill_name}.md"
        echo "   ✓ ${skill_name}"
    fi
done

# 5. Dictionary 파일 복사 (JSON 사전 + HTML 리포트 템플릿)
echo "📋 Dictionary 파일 복사 중..."
for dict_file in "${SCRIPT_DIR}/dictionary"/*.json "${SCRIPT_DIR}/dictionary"/*.html; do
    if [ -f "$dict_file" ]; then
        cp "$dict_file" "$DICT_DIR/"
        echo "   ✓ $(basename "$dict_file")"
    fi
done

# 5.5 Scripts 파일 복사 (HTML 리포트 생성기 — 단계 11)
echo "📋 Scripts 파일 복사 중..."
for script_file in "${SCRIPT_DIR}/scripts"/*.py; do
    if [ -f "$script_file" ]; then
        cp "$script_file" "$SCRIPTS_DIR/"
        echo "   ✓ $(basename "$script_file")"
    fi
done

# 5.6 라이선스·고지 복사 (패키지 루트)
echo "📋 LICENSE/NOTICE 복사 중..."
for lic_file in LICENSE NOTICE; do
    if [ -f "${SCRIPT_DIR}/${lic_file}" ]; then
        cp "${SCRIPT_DIR}/${lic_file}" "$SKILL_DIR/"
        echo "   ✓ ${lic_file}"
    fi
done

# 6. Docs 파일 복사 (sub-skill에서 참조하는 문서)
echo "📋 Docs 파일 복사 중..."
DOCS_FILES=(
    "SCHEMA_V1.3_ENFORCEMENT.md"
    "claude-threat-scan-json-schema-v1.3.md"
    "SCHEMA_V1.2_ENFORCEMENT.md"
    "claude-threat-scan-json-schema-v1.2.md"
    "claude_threat_scan_prompt_v_2.md"
)
for doc_file in "${DOCS_FILES[@]}"; do
    src="${SCRIPT_DIR}/docs/${doc_file}"
    if [ -f "$src" ]; then
        cp "$src" "$DOCS_DIR/"
        echo "   ✓ ${doc_file}"
    else
        echo "   ⚠ ${doc_file} 누락 (경고)"
    fi
done

# 7. Sub-skill 내 상대 경로 치환 (dist 구조에 맞게)
#    원본: ../../docs/FILE  → 변환: ../docs/FILE
#    원본: ../../dictionary/FILE → 변환: ../dictionary/FILE
echo "🔗 Sub-skill 파일 내 경로 치환 중..."
for md_file in "${SUB_SKILLS_DIR}"/*.md; do
    if [ -f "$md_file" ]; then
        # macOS(BSD sed)·Linux(GNU sed) 양쪽 호환을 위해 -i 대신 임시파일 방식 사용
        sed -e 's|../../docs/|../docs/|g' -e 's|../../dictionary/|../dictionary/|g' \
            "$md_file" > "${md_file}.tmp" && mv "${md_file}.tmp" "$md_file"
    fi
done
echo "   ✓ 경로 치환 완료"

# 8. ZIP 생성 (폴더째로 압축)
echo ""
echo "📦 ZIP 파일 생성 중..."
cd "$DIST_DIR"
zip -r "$ZIP_FILE" "$(basename "$SKILL_DIR")/" -x "*.DS_Store"
cd "$SCRIPT_DIR"

echo ""
echo "============================================================"
echo "🎉 빌드 완료!"
echo ""
echo "📄 ZIP 파일: ${ZIP_FILE}"
echo "📏 크기: $(du -h "$ZIP_FILE" | cut -f1)"
echo ""
echo "📋 내용물:"
unzip -l "$ZIP_FILE" | tail -n +4 | sed '$d' | sed '$d'
echo ""
echo "🚀 업로드 방법:"
echo "   Claude Desktop → Settings → Capabilities → Skills"
echo "   → Upload 클릭 → claude-threat-scan.zip 선택"
echo "============================================================"
