#!/usr/bin/env python3
"""
validate_report_schema.py — 리포트 전체 스키마 결정론 검증기 (stdlib-only, v2.5.1 / D3).

단계 11(HTML 생성, 셸 허용) 직전에 실행해 Schema V1.4 준수를 기계 검증한다.
Desktop 최초의 결정론 강제 게이트이며, Code 모드도 compliance validator와 나란히 실행한다.
(compliance_tags 자체 검증은 validate_compliance_tags.py 소관 — 여기서 중복하지 않는다.)

사용법:
  python3 validate_report_schema.py <report.json> [--json]

종료 코드: 0=clean, 1=errors, 2=warnings-only.
"""
import argparse
import json
import re
import sys

# 배열 → 허용 finding ID prefix
ID_PREFIX = {
    "static_code_findings": ("STATIC-",),
    "binary_analysis_findings": ("BIN-",),
    "skill_risk_findings": ("SKILL-",),
    "agent_policy_findings": ("AGENT-",),
    "sensitive_patterns": ("SENS-",),
    "prompt_optimization": ("OPT-",),
    "relationship_findings": ("REL-",),
    "model_validity_findings": ("MODEL-",),
    "recommendations": ("REC-",),
}
SBOM_ID_PREFIX = {
    "vulnerability_findings": ("VULN-",),
    "license_findings": ("LIC-",),
    "version_risk_findings": ("VER-",),
    "supply_chain_findings": ("SUPPLY-",),
}
# sbom 비정본 배열명 → 정본
SBOM_ALIASES = {
    "vulnerabilities": "vulnerability_findings",
    "license_issues": "license_findings",
    "supply_chain_risks": "supply_chain_findings",
    "version_risks": "version_risk_findings",
}
VERDICT_OK = {"INSTALL_OK", "REVIEW", "DISABLE", "REMOVE"}
ENUM_FIELDS = ["severity", "status", "verdict", "security_verdict", "priority",
               "confidence", "model_effectiveness", "edge_type", "component_type",
               "target_type", "pattern_type", "risk_level", "gitignore_status"]
# 서술(완역 대상) 필드
PROSE_FIELDS = ["description", "recommendation", "deep_dive_result", "detail",
                "issue", "rationale", "risk_summary", "analysis"]
REC_ALIASES = {"title": "action", "description": "rationale", "references": "finding_ids"}
RS_FORBIDDEN = {"name", "tech_stack", "total_findings", "critical", "high",
                "medium", "low", "info"}
HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"[A-Za-z]")


def has_hangul_ratio(texts):
    """서술 텍스트 묶음의 한글/(한글+라틴) 비율. 텍스트 없으면 None."""
    h = lat = 0
    for t in texts:
        if not isinstance(t, str):
            continue
        h += len(HANGUL.findall(t))
        lat += len(LATIN.findall(t))
    tot = h + lat
    if tot < 40:      # 표본 부족 — 판정 보류
        return None
    return h / tot


def all_findings(report):
    """(array_name, finding) 순회 — sbom 포함."""
    for arr in ID_PREFIX:
        for f in report.get(arr, []) or []:
            if isinstance(f, dict):
                yield arr, f
    sbom = report.get("sbom_analysis")
    if isinstance(sbom, dict):
        for arr in SBOM_ID_PREFIX:
            for f in sbom.get(arr, []) or []:
                if isinstance(f, dict):
                    yield "sbom_analysis." + arr, f


def check_half(report, half, errors, warnings):
    if not isinstance(report, dict):
        return
    # ID prefix
    for arr, prefixes in ID_PREFIX.items():
        for f in report.get(arr, []) or []:
            if isinstance(f, dict):
                fid = str(f.get("id", ""))
                if fid and not fid.startswith(prefixes):
                    errors.append("%s.%s: id '%s' prefix != %s" % (half, arr, fid, prefixes))
    # recommendations 비정본 별칭 + 필수 필드
    for i, r in enumerate(report.get("recommendations", []) or []):
        if not isinstance(r, dict):
            continue
        for alias, canon in REC_ALIASES.items():
            if alias in r and canon not in r:
                errors.append("%s.recommendations[%d]: 비정본 필드 '%s' (정본 '%s')"
                              % (half, i, alias, canon))
        for req in ("action", "rationale", "finding_ids"):
            if req not in r:
                errors.append("%s.recommendations[%d]: 필수 필드 '%s' 누락" % (half, i, req))
        if isinstance(r.get("finding_ids"), list) and not r["finding_ids"]:
            errors.append("%s.recommendations[%d]: finding_ids 빈 배열" % (half, i))
    # sbom 비정본 배열명
    sbom = report.get("sbom_analysis")
    if isinstance(sbom, dict):
        for alias, canon in SBOM_ALIASES.items():
            if alias in sbom:
                errors.append("%s.sbom_analysis: 비정본 배열명 '%s' (정본 '%s')"
                              % (half, alias, canon))
        # sbom-level verdict 발명 (APPROVE 등)
        sv = sbom.get("verdict")
        if sv is not None and str(sv) not in VERDICT_OK:
            errors.append("%s.sbom_analysis.verdict '%s' 발명 값 (4종만 허용)" % (half, sv))
        # sbom ID prefix
        for arr, prefixes in SBOM_ID_PREFIX.items():
            for f in sbom.get(arr, []) or []:
                if isinstance(f, dict):
                    fid = str(f.get("id", ""))
                    if fid and not fid.startswith(prefixes):
                        errors.append("%s.sbom.%s: id '%s' prefix != %s" % (half, arr, fid, prefixes))
    # graph_verdict 정본 필드
    rs = report.get("repository_summary", {})
    if isinstance(rs, dict):
        gv = rs.get("graph_verdict")
        if isinstance(gv, dict):
            if "security_verdict" not in gv and "verdict" in gv:
                errors.append("%s.graph_verdict: 'verdict' → 정본 'security_verdict' 필요" % half)
            if "rationale" not in gv and ("propagation_summary" in gv or "summary" in gv):
                errors.append("%s.graph_verdict: 'rationale' 누락 (propagation_summary/summary만 존재)" % half)
        # 임의 필드 경고
        for fld in RS_FORBIDDEN:
            if fld in rs:
                warnings.append("%s.repository_summary: 비정본 필드 '%s'" % (half, fld))
    # finding verdict 화이트리스트 + code_fix 객체 구조
    for arr, f in all_findings(report):
        v = f.get("verdict")
        if v is not None and str(v) not in VERDICT_OK:
            errors.append("%s.%s[%s].verdict '%s' 발명/비정본 (4종만)"
                          % (half, arr, f.get("id", "?"), v))
        if "code_fix" in f and not isinstance(f["code_fix"], dict):
            errors.append("%s.%s[%s].code_fix가 %s (정본: 객체 {language,before,after,note})"
                          % (half, arr, f.get("id", "?"), type(f["code_fix"]).__name__))


def main(argv=None):
    p = argparse.ArgumentParser(description="Validate report schema (v2.5.1 D3)")
    p.add_argument("report")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    try:
        data = json.load(open(args.report, encoding="utf-8"))
    except Exception as e:
        print("[ERROR] cannot read report: %s" % e, file=sys.stderr)
        return 1

    errors, warnings = [], []
    en = data.get("english_report", data)
    ko = data.get("korean_report")

    check_half(en, "english_report", errors, warnings)
    if isinstance(ko, dict):
        check_half(ko, "korean_report", errors, warnings)

        # enum EN/KO 동일성 + 한글 값(번역됨) 감지
        def enum_pairs(rep):
            out = {}
            for arr, f in all_findings(rep):
                for k in ENUM_FIELDS:
                    if k in f and isinstance(f[k], str):
                        out[(arr, str(f.get("id", "")), k)] = f[k]
            return out
        en_e, ko_e = enum_pairs(en), enum_pairs(ko)
        for key, kov in ko_e.items():
            if HANGUL.search(kov):
                errors.append("korean_report enum %s = '%s' 번역됨 (enum은 영문 원형)" % (key[1:], kov))
            env = en_e.get(key)
            if env is not None and env != kov:
                errors.append("enum EN/KO 불일치 %s: EN='%s' KO='%s'" % (key[1:], env, kov))

        # KR prose 완역 휴리스틱
        texts = []
        for arr, f in all_findings(ko):
            for pf in PROSE_FIELDS:
                if isinstance(f.get(pf), str):
                    texts.append(f[pf])
        ratio = has_hangul_ratio(texts)
        if ratio is not None:
            if ratio < 0.30:
                errors.append("korean_report prose 미번역 의심: 한글 비율 %.0f%% (<30%%)" % (ratio * 100))
            elif ratio < 0.60:
                warnings.append("korean_report prose 부분 번역 의심: 한글 비율 %.0f%%" % (ratio * 100))

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings,
                          "error_count": len(errors), "warning_count": len(warnings)},
                         ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print("[ERROR] " + e)
        for w in warnings:
            print("[WARN]  " + w)
        if not errors and not warnings:
            print("[OK] report schema valid (0 errors, 0 warnings)")
        else:
            print("\n%d error(s), %d warning(s)" % (len(errors), len(warnings)))

    return 1 if errors else (2 if warnings else 0)


if __name__ == "__main__":
    sys.exit(main())
