# threat-scan-security — Patch proposal (v2.4.0 → v2.4.1)

**Title:** Fix multi-minute stall / hang in the Korean translation step (단계 10)
**Component:** `tss-translator` agent + `threat-scan-orchestrator` Phase 3
**Severity:** High (pipeline reliably hangs on medium/large reports; each run wastes 30+ min and requires manual kill + rescue)
**Reporter:** ReviewOS-security scan, 2026-07-14

---

## 1. Symptom

During `/threat-scan`, the pipeline consistently stalls at **Step 10 (`tss-translator`)**.
The translator subagent reads the English report, prints "이제 완전한 bilingual JSON을
작성합니다", then produces **no further transcript growth for 30+ minutes**. The output
file is never written, so the orchestrator's file-existence checkpoint never passes and the
run appears hung. Observed twice in a row on the same report before a manual workaround
succeeded.

## 2. Root cause (confirmed, not speculative)

Two compounding factors baked into the agent contract:

1. **The translator re-emits `english_report` verbatim.**
   `agents/tss-translator.md` step 4 instructs it to `Write the complete bilingual JSON
   { scan_metadata, english_report, korean_report }`. The English half (~40–50K tokens)
   already exists in `step9-english.json`; forcing the LLM to copy it into its own output
   doubles the generation size for zero informational gain.

2. **One monolithic `Write` call exceeds the single-response output-token ceiling.**
   For a report with ~30 findings + 9 relationship findings (long paragraphs each) + 11
   recommendations, the bilingual document is ~178 KB. Emitted as a single `Write` `content`
   argument, the combined english+korean output exceeds the model's single-response output
   limit (~64K tokens for Sonnet). The `tool_use` block never completes → file never written
   → transcript flatlines → looks like a hang.

The agent has `tools: Read, Write` (no Bash), so it **cannot** do a deterministic merge —
it is architecturally forced to regenerate the English half through the model.

**Proof:** Restricting the agent to emit **only** `korean_report{}` (≈40K tokens, within a
single-response budget) completed on the first try (335 s, valid JSON). The English half was
then merged deterministically via a 6-line Python script (instant). Halving the per-call
output removed the stall entirely.

## 3. Fix

Principle: **(a) the LLM never regenerates the English report, and (b) no single giant Write.**

### 3.1 `agents/tss-translator.md` — emit korean_report only

```diff
-4. Write the complete bilingual JSON `{ "scan_metadata": {...}, "english_report": {...}, "korean_report": {...} }` to `OUTPUT_PATH` (provided in prompt).
-5. Return: `Wrote <OUTPUT_PATH>; bilingual report complete`
+4. Write **ONLY** the translated `korean_report{}` object (a single top-level JSON object
+   whose keys mirror `english_report` exactly) to `OUTPUT_PATH` (e.g. `.../step10-korean.json`).
+   Do **NOT** re-emit `english_report` or the bilingual wrapper — the orchestrator merges
+   English + Korean deterministically afterward. Re-emitting English doubles output and
+   overflows the single-response token limit (the historical cause of multi-minute stalls).
+5. Return: `Wrote <OUTPUT_PATH>; korean_report complete`

 ## Rules
 - No Bash, no code execution. Write only to OUTPUT_PATH.
+- Output = `korean_report{}` only. Never copy the English report through the model.
 - 모든 finding 카테고리·구조는 Schema V1.3 그대로. 번역은 value 텍스트만, key 불변.
+- severity / status / verdict / edge_type / component_type / model_effectiveness enum 값과
+  id·file 경로·code_fix 코드·CVE·라이선스·패키지명은 원문(영문/리터럴) 그대로 둔다.
```

`tools:` stays `Read, Write` — the no-code-execution sandbox rule for steps 1–10 is preserved.

### 3.2 `skills/threat-scan-orchestrator/SKILL.md` — Phase 3 deterministic merge

Translator now writes `korean_report` to `SCAN_TMP/step10-korean.json`; a Bash step merges
`step9-english.json` + `step10-korean.json` into the final `scanreport-*.json`.

```diff
 2. `tss-translator` 프롬프트:
    - INPUT_PATH:  .../tss.XXXX/step9-english.json
-   - OUTPUT_PATH: .../scanreport-<TS>.json   (final bilingual, single giant write)
+   - OUTPUT_PATH: .../tss.XXXX/step10-korean.json   (korean_report only)
+3. 결정론적 병합 (Bash, LLM 재생성 없음):
```

```python
python3 - <<'PY'
import json
D="/var/folders/.../tss.XXXX"                       # SCAN_TMP
OUT="/.../scanreport-<TIMESTAMP>.json"              # OUT_DIR + /scanreport- + TIMESTAMP + .json
e=json.load(open(D+"/step9-english.json"))
kraw=open(D+"/step10-korean.json").read().replace("</content>","").strip()  # defensive tail-artifact strip
k=json.loads(kraw)
er=e.get("english_report", e)
final={
  "output_filename": OUT.split("/")[-1],
  "scan_metadata": e.get("scan_metadata", {}),
  "english_report": er,
  "korean_report": k,
}
json.dump(final, open(OUT,"w"), ensure_ascii=False, indent=2)
print("MERGED", OUT)
PY
```

Final validation (unchanged path, now also asserts both halves exist):

```bash
test -f "/.../scanreport-<TS>.json" \
  && python3 -c "import json,sys;d=json.load(open(sys.argv[1]));assert d['english_report'] and d['korean_report'];print('REPORT OK')" "/.../scanreport-<TS>.json" \
  || echo "FAIL: bilingual report not written"
```

Phase 4 (`tss-html-report`) is unchanged — it still consumes the final `scanreport-*.json`.

## 4. Claude Desktop (sandbox, no Bash) note

Desktop mode cannot run the merge script. There, the orchestrator model assembles the final
file itself from `step9` (English) + `step10` (Korean) — but it must **copy** `english_report`
from the step9 file verbatim, never re-translate/regenerate it. The output-halving benefit
still applies because the translator only ever produced the Korean half. A fully
Bash-free path could alternatively route the merge into the script-allowed Step 11
(`tss-html-report`) generator, emitting the merged JSON as a side output.

## 5. Impact

- Translation step output cut ~50% → stays within single-response token budget → **no more hangs**.
- Merge is deterministic and instant; also fixes a latent truncation risk on very large reports.
- No schema change; final `scanreport-*.json` shape is identical for downstream consumers.

## 6. Files changed

| File | Change |
|------|--------|
| `agents/tss-translator.md` | Emit `korean_report{}` only; forbid English re-emission |
| `skills/threat-scan-orchestrator/SKILL.md` | Phase 3: korean-only OUTPUT_PATH + deterministic Bash merge + stronger validation |

Applied in-place to the local plugin cache
(`~/.claude/plugins/cache/threat-scan-security-marketplace/threat-scan-security/2.4.0/`).
⚠️ A plugin update/reinstall of 2.4.0 will overwrite these; carry this patch forward or land it upstream as 2.4.1.
