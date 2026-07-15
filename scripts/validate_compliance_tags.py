#!/usr/bin/env python3
"""
validate_compliance_tags.py — Schema V1.4 compliance_tags 검증기 (stdlib-only, 결정론).

SCHEMA_V1.4_COMPLIANCE_TAGS.md §3.3 규칙 구현:
  - regex hard-fail, unknown-control-ID warn, cardinality(≤4)/uniqueness,
    EN/KO parity(8 허용 배열), 금지 변형 탐지, 금지 배치 탐지.

사용법:
  python3 validate_compliance_tags.py <report.json> [--json]

종료 코드: 0=clean, 1=errors, 2=warnings-only.
"""
import argparse
import json
import re
import sys

TAG_RE = re.compile(r"^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$")

KNOWN = {
    "KISA": {f"1_{i}" for i in range(1, 18)} | {f"2_{i}" for i in range(1, 17)}
          | {"3_1", "3_2", "4_1", "4_2", "4_3"}
          | {f"5_{i}" for i in range(1, 6)} | {f"6_{i}" for i in range(1, 5)}
          | {"7_1", "7_2"},
    "AILLM": {f"8_{i}" for i in range(1, 10)},
    "TA": {"T_A1", "T_C3", "T_D1", "T_D2", "T_D3", "T_E1",
           "T_I1", "T_I2", "T_I3", "A_B1"},
}

# finding 객체에 태그가 허용되는 8개 배열
PERMITTED_ARRAYS = [
    "static_code_findings", "binary_analysis_findings", "skill_risk_findings",
    "agent_policy_findings", "sensitive_patterns", "relationship_findings",
    "model_validity_findings",
]
# sbom_analysis 내부 finding 배열
SBOM_FINDING_ARRAYS = [
    "vulnerabilities", "version_risk_findings", "license_issues",
    "supply_chain_risks", "findings",
]
# 태그 배치가 금지된 위치
FORBIDDEN_PLACEMENT = ["prompt_optimization", "recommendations"]
# 금지 변형 필드명
FORBIDDEN_VARIANTS = {
    "tags", "compliance", "kisa_tags", "kisaTags", "control",
    "controls", "control_mapping", "owasp_tags",
}


def validate_tag_list(tags, where, errors, warnings):
    if not isinstance(tags, list):
        errors.append(f"{where}: compliance_tags must be an array")
        return
    if len(tags) > 4:
        errors.append(f"{where}: cardinality>4 ({len(tags)})")
    if len(set(tags)) != len(tags):
        errors.append(f"{where}: duplicate tags {tags}")
    for t in tags:
        if not isinstance(t, str) or not TAG_RE.match(t):
            errors.append(f"{where}: format violation: {t!r}")
            continue
        ns = t.split("-", 1)[0][1:]
        cid = t.split("-", 1)[1]
        if cid not in KNOWN.get(ns, set()):
            warnings.append(f"{where}: unknown control id {t}")


def check_finding(obj, where, errors, warnings):
    if not isinstance(obj, dict):
        return
    for variant in FORBIDDEN_VARIANTS:
        if variant in obj:
            errors.append(f"{where}: prohibited field variant '{variant}' "
                          f"(use compliance_tags)")
    if "compliance_tags" in obj:
        validate_tag_list(obj["compliance_tags"], where + ".compliance_tags",
                          errors, warnings)


def iter_report(report, half, errors, warnings):
    if not isinstance(report, dict):
        return
    # permitted arrays
    for arr in PERMITTED_ARRAYS:
        for i, obj in enumerate(report.get(arr, []) or []):
            check_finding(obj, f"{half}.{arr}[{i}]", errors, warnings)
    # sbom findings
    sbom = report.get("sbom_analysis")
    if isinstance(sbom, dict):
        for arr in SBOM_FINDING_ARRAYS:
            for i, obj in enumerate(sbom.get(arr, []) or []):
                check_finding(obj, f"{half}.sbom_analysis.{arr}[{i}]",
                              errors, warnings)
    # forbidden placement: compliance_tags must NOT appear here
    for arr in FORBIDDEN_PLACEMENT:
        for i, obj in enumerate(report.get(arr, []) or []):
            if isinstance(obj, dict) and "compliance_tags" in obj:
                errors.append(f"{half}.{arr}[{i}]: compliance_tags not permitted here")
    rs = report.get("repository_summary")
    if isinstance(rs, dict) and "compliance_tags" in rs:
        errors.append(f"{half}.repository_summary: compliance_tags not permitted here")


def collect_tags_by_finding(report):
    """EN/KO parity: map finding id → compliance_tags across permitted arrays."""
    out = {}
    if not isinstance(report, dict):
        return out
    def add(arr_name, objs):
        for obj in objs or []:
            if isinstance(obj, dict) and "compliance_tags" in obj:
                key = f"{arr_name}:{obj.get('id', id(obj))}"
                out[key] = obj["compliance_tags"]
    for arr in PERMITTED_ARRAYS:
        add(arr, report.get(arr, []))
    sbom = report.get("sbom_analysis")
    if isinstance(sbom, dict):
        for arr in SBOM_FINDING_ARRAYS:
            add("sbom." + arr, sbom.get(arr, []))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="Validate Schema V1.4 compliance_tags.")
    p.add_argument("report", help="Path to scanreport JSON")
    p.add_argument("--json", action="store_true", help="Machine-readable JSON summary")
    args = p.parse_args(argv)

    try:
        data = json.load(open(args.report, encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] cannot read report: {e}", file=sys.stderr)
        return 1

    errors, warnings = [], []
    en = data.get("english_report", data)
    ko = data.get("korean_report")

    iter_report(en, "english_report", errors, warnings)
    if isinstance(ko, dict):
        iter_report(ko, "korean_report", errors, warnings)
        # EN/KO parity
        en_map = collect_tags_by_finding(en)
        ko_map = collect_tags_by_finding(ko)
        for key, en_tags in en_map.items():
            ko_tags = ko_map.get(key)
            if ko_tags is None:
                warnings.append(f"parity: {key} has tags in EN but not in KO")
            elif en_tags != ko_tags:
                errors.append(f"parity: {key} EN{en_tags} != KO{ko_tags} "
                              f"(tags must be byte-identical)")

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings,
                          "error_count": len(errors),
                          "warning_count": len(warnings)},
                         ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print(f"[ERROR] {e}")
        for w in warnings:
            print(f"[WARN]  {w}")
        if not errors and not warnings:
            print("[OK] compliance_tags valid (0 errors, 0 warnings)")
        else:
            print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")

    if errors:
        return 1
    if warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
