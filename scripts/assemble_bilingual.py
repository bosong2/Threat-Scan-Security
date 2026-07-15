#!/usr/bin/env python3
"""
assemble_bilingual.py — 분할 번역 조각(step10-frag-*.json)을 최종 bilingual JSON으로 조립.

단계 10.5 — 결정론적 셸 예외 (단계 0·11과 동일 성격).
LLM 추론 없음. 표준 라이브러리만 사용. 동일 입력 → 동일 출력.

사용법:
  python3 assemble_bilingual.py \
      --english <step9-english.json> \
      --frags <step10-frag-1.json> <step10-frag-2.json> ... \
      --metadata <scan_metadata_json_string_or_file> \
      --out <output_path>

  환경 변수 SCAN_TMP 가 설정돼 있으면 --frags 생략 시 자동으로
  $SCAN_TMP/step10-frag-*.json 을 검색한다.
"""
import argparse
import glob
import json
import os
import sys

# 5-group category mapping (matches orchestrator split groups)
CATEGORY_GROUPS = [
    ["repository_summary"],
    ["static_code_findings", "binary_analysis_findings"],
    ["skill_risk_findings", "agent_policy_findings"],
    ["sensitive_patterns", "prompt_optimization", "sbom_analysis"],
    ["relationship_findings", "model_validity_findings", "recommendations"],
]
ALL_CATEGORIES = [k for grp in CATEGORY_GROUPS for k in grp]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def count_items(report, key):
    """Return len() for array keys, 1 for object keys, 0 if missing."""
    v = report.get(key)
    if v is None:
        return 0
    if isinstance(v, list):
        return len(v)
    if isinstance(v, dict):
        return 1
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Assemble split translation fragments into final bilingual JSON.")
    p.add_argument("--english", required=True,
                   help="Path to step9-english.json (english_report source)")
    p.add_argument("--frags", nargs="*", default=None,
                   help="Fragment JSON files (step10-frag-*.json). "
                        "Auto-detected from $SCAN_TMP if omitted.")
    p.add_argument("--out", required=True,
                   help="Output path for final bilingual JSON")
    p.add_argument("--scan-metadata", dest="scan_metadata", default=None,
                   help="Path to scan_metadata JSON file, or inline JSON string. "
                        "If omitted, read from english source root.")
    args = p.parse_args(argv)

    # ── Load english report ────────────────────────────────────────────────
    eng_src = load_json(args.english)
    english_report = eng_src.get("english_report", eng_src)
    # Prefer scan_metadata from root of english file
    scan_metadata = eng_src.get("scan_metadata", {})

    # Override with explicit --scan-metadata if provided
    if args.scan_metadata:
        if os.path.isfile(args.scan_metadata):
            scan_metadata = load_json(args.scan_metadata)
        else:
            try:
                scan_metadata = json.loads(args.scan_metadata)
            except json.JSONDecodeError:
                sys.exit("[ERROR] --scan-metadata: not a valid JSON string or file path")

    # ── Collect fragment files ─────────────────────────────────────────────
    frag_files = args.frags
    if not frag_files:
        scan_tmp = os.environ.get("SCAN_TMP", "")
        if scan_tmp:
            frag_files = sorted(glob.glob(os.path.join(scan_tmp, "step10-frag-*.json")))
        if not frag_files:
            sys.exit("[ERROR] No fragment files provided and none found via $SCAN_TMP")

    # ── Merge korean fragments ─────────────────────────────────────────────
    korean_report = {}
    for fp in frag_files:
        if not os.path.isfile(fp):
            sys.exit("[ERROR] Fragment file not found: %s" % fp)
        frag = load_json(fp)
        kr_chunk = frag.get("korean_report", frag)
        for key, val in kr_chunk.items():
            if key in korean_report:
                # Merge arrays
                if isinstance(korean_report[key], list) and isinstance(val, list):
                    korean_report[key].extend(val)
                else:
                    # Object: update (later fragment wins per-key)
                    if isinstance(korean_report[key], dict) and isinstance(val, dict):
                        korean_report[key].update(val)
                    else:
                        korean_report[key] = val
            else:
                korean_report[key] = val

    # ── Validation: EN/KR counts ───────────────────────────────────────────
    mismatches = []
    for key in ALL_CATEGORIES:
        en_count = count_items(english_report, key)
        kr_count = count_items(korean_report, key)
        # Allow korean to be absent when english is also absent
        if en_count == 0 and kr_count == 0:
            continue
        if en_count != kr_count:
            mismatches.append("  %s: EN=%d KR=%d" % (key, en_count, kr_count))

    if mismatches:
        print("[WARNING] EN/KR count mismatches detected:", file=sys.stderr)
        for m in mismatches:
            print(m, file=sys.stderr)
        # Non-fatal warning — partial translation is better than no report.
        # Change to sys.exit(1) to enforce strict parity.

    # ── Build final bilingual JSON ─────────────────────────────────────────
    output = {
        "scan_metadata": scan_metadata,
        "english_report": english_report,
        "korean_report": korean_report,
    }
    # Preserve output_filename if present
    if "output_filename" in eng_src:
        output["output_filename"] = eng_src["output_filename"]

    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        sys.exit("[ERROR] Output directory does not exist: %s" % out_dir)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    total_en = sum(count_items(english_report, k) for k in ALL_CATEGORIES)
    total_kr = sum(count_items(korean_report, k) for k in ALL_CATEGORIES)
    print("[OK] assemble_bilingual: %s (EN=%d items, KR=%d items, %d fragments)"
          % (args.out, total_en, total_kr, len(frag_files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
