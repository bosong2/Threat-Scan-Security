# Compliance Tag Map : Distilled Pre-Scan Directive (CTID-D v1.1)

> **Role**: The ONLY tagging context injected into pipeline stages 1–8 of `threat-scan-security`.
> **Companion**: `compliance-tagging-deepdive.md` (stage 8.5 verification). Full rationale: CTID v1.0.
> **Schema**: emits `compliance_tags` per Schema V1.4. Do not emit the field if the runtime schema is < V1.4.
> **Framework pinning**: KISA 2021 (49 controls, fixed) · OWASP Top 10 for LLM Applications 2025 · CWE v4.20 · MITRE ATLAS (2025-10 agentic update). References float to latest editions; tag IDs never change.

---

## 1. Emission Rules (all analyzers, stages 1–8)

1. Assign `compliance_tags` at the moment each finding object is created.
2. Grammar: `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$` · 0–4 unique tags · primary (root-cause) tag first.
3. Tag by root cause, not symptom. If no governed control matches, emit `[]`. Never approximate.
4. CWE / OWASP-LLM / ATLAS identifiers are prose references (put in `description` or `recommendation`), never `#`-tags.
5. `AILLM` tags: only when the target has LLM/agent features. `TA` tags: only on IaC/config artifact evidence.
6. Tags are classification metadata. They never justify exposing evidence beyond existing masking rules.

## 2. Stage-to-Range Map

| Stage | Array | Expected ranges |
|---|---|---|
| 2 static-code-analyzer | `static_code_findings` | `#KISA-1_*`–`#KISA-7_*`, `#AILLM-*` (LLM code paths), `#TA-*` (IaC files) |
| 3 binary-analyzer | `binary_analysis_findings` | `#KISA-2_15`, `#KISA-6_2`, `#KISA-7_2` |
| 4 skill-security-analyzer | `skill_risk_findings` | `#KISA-1_*`, `#AILLM-8_1`–`8_4`, `8_7` |
| 4.5 / 4.6 graph·model | `relationship_findings` / `model_validity_findings` | `[]` default; `#KISA-7_2` for deprecated model/API where applicable |
| 5 sensitive-pattern-matcher | `sensitive_patterns` | `#KISA-2_5`, `2_6`, `2_12`, `2_13`, `#AILLM-8_4` |
| 6 agent-policy-verifier | `agent_policy_findings` | `#AILLM-8_1`, `8_2`, `8_5`, `8_6`, `8_7` |
| 8 sbom-analyzer | `sbom_analysis` findings | `#KISA-7_2`, `#KISA-2_15`, `#AILLM-8_9`, `#TA-A_B1` |

## 3. KISA Tag Map (49, fixed)

### §1 Input Validation & Representation
| Tag | Root-cause trigger | Ref |
|---|---|---|
| `#KISA-1_1` | external input concatenated into SQL query | CWE-89 |
| `#KISA-1_2` | external input reaches dynamic execution (eval-family) | CWE-94 |
| `#KISA-1_3` | user input in file path / resource id (`../`) | CWE-22/73 |
| `#KISA-1_4` | unescaped input to HTML/DOM output | CWE-79 |
| `#KISA-1_5` | OS command built from external input | CWE-78 |
| `#KISA-1_6` | upload without extension+MIME+magic validation | CWE-434 |
| `#KISA-1_7` | external input in redirect target | CWE-601 |
| `#KISA-1_8` | XML parser resolves DTD/external entities | CWE-611 |
| `#KISA-1_9` | unvalidated input in XPath/XQuery | CWE-91 |
| `#KISA-1_10` | unvalidated input in LDAP filter | CWE-90 |
| `#KISA-1_11` | state-changing request without anti-CSRF | CWE-352 |
| `#KISA-1_12` | server fetches user-supplied URL | CWE-918 |
| `#KISA-1_13` | CR/LF from input reaches HTTP headers | CWE-113 |
| `#KISA-1_14` | untrusted integers in allocation/loop math | CWE-190 |
| `#KISA-1_15` | auth/authz trusts tamperable client data (headers/roles/flags) | CWE-807 |
| `#KISA-1_16` | buffer copy without length check | CWE-120/787 |
| `#KISA-1_17` | external input used as format string | CWE-134 |

### §2 Security Functions
| Tag | Root-cause trigger | Ref |
|---|---|---|
| `#KISA-2_1` | sensitive function/endpoint reachable unauthenticated; exposed admin/API docs | CWE-306 |
| `#KISA-2_2` | object access without ownership/role check (IDOR) | CWE-285 |
| `#KISA-2_3` | over-permissive file/dir/config permissions | CWE-732 |
| `#KISA-2_4` | MD5/SHA1/DES/RC4 or equivalent weak crypto | CWE-327 |
| `#KISA-2_5` | plaintext sensitive data in transit/rest/log | CWE-311 |
| `#KISA-2_6` | secrets/keys/credentials hardcoded in source | CWE-798 |
| `#KISA-2_7` | RSA < 2048 or otherwise insufficient key length | CWE-326 |
| `#KISA-2_8` | non-CSPRNG in security context | CWE-330 |
| `#KISA-2_9` | no password complexity/length policy | CWE-521 |
| `#KISA-2_10` | signature/JWT verification skipped; `alg:none` | CWE-347 |
| `#KISA-2_11` | certificate validation disabled/partial (`verify=false`) | CWE-295 |
| `#KISA-2_12` | session/authz data in readable persistent cookies | CWE-539 |
| `#KISA-2_13` | credentials/internal info in comments | CWE-615 |
| `#KISA-2_14` | unsalted / fast password hashing | CWE-759 |
| `#KISA-2_15` | remote code/deps fetched without integrity/signature check | CWE-494 |
| `#KISA-2_16` | no brute-force rate limit/lockout | CWE-307 |

### §3–§7
| Tag | Root-cause trigger | Ref |
|---|---|---|
| `#KISA-3_1` | TOCTOU gap; concurrent duplicate mutation | CWE-367 |
| `#KISA-3_2` | unbounded loop/recursion; catastrophic regex (ReDoS) | CWE-835/1333 |
| `#KISA-4_1` | stack trace/internal path exposed to client | CWE-209 |
| `#KISA-4_2` | unchecked return values; missing error handling | CWE-755/252 |
| `#KISA-4_3` | broad/empty handlers hiding failures | CWE-396/460 |
| `#KISA-5_1` | null/None dereference without check | CWE-476 |
| `#KISA-5_2` | leaked file/socket/DB handles | CWE-772/404 |
| `#KISA-5_3` | reuse after close/free | CWE-416 |
| `#KISA-5_4` | read before assignment | CWE-457 |
| `#KISA-5_5` | unsafe deserialization of external input | CWE-502 |
| `#KISA-6_1` | session/global state bleed between users | CWE-488 |
| `#KISA-6_2` | debug/test code, endpoints, source maps in prod | CWE-489 |
| `#KISA-6_3` | internal mutable reference returned | CWE-495 |
| `#KISA-6_4` | external mutable reference stored internally | CWE-496 |
| `#KISA-7_1` | hostname/DNS trusted for access decisions | CWE-247/350 |
| `#KISA-7_2` | deprecated/dangerous API; known-vulnerable dependency | CWE-477 |

## 4. AILLM Tag Map (v1.1 : anchored to OWASP LLM Top 10 2025 / CWE 4.20 / MITRE ATLAS)

> Anchors verified against genai.owasp.org and cwe.mitre.org, access date 2026-07-15.
> `8_1`–`8_6` are the original fixed set; `8_7`–`8_9` are v1.1 appended controls (never renumber).

| Tag | Weakness | Root-cause trigger | OWASP LLM 2025 | CWE | ATLAS |
|---|---|---|---|---|---|
| `#AILLM-8_1` | Prompt Injection (direct) | user input concatenated into system prompt / instruction channel | LLM01 | CWE-1427 | AML.T0051.000 |
| `#AILLM-8_2` | Indirect Prompt Injection | instructions in fetched URLs/files/RAG content trusted as commands; LLM-triggered actions without user approval | LLM01 | CWE-1427 | AML.T0051.001 |
| `#AILLM-8_3` | Trusting LLM Output | LLM-generated code/SQL/command/URL executed or rendered without validation/allow-listing | LLM05 | CWE-1426 (downstream: CWE-94/78/89/79) | : |
| `#AILLM-8_4` | Sensitive Data in Context | secrets/PII/other-user data injected into prompts, system prompts, or LLM logs | LLM02 · LLM07 | CWE-200 (secrets: CWE-798 secondary) | AML.T0056 · AML.T0057 |
| `#AILLM-8_5` | Unbounded Output / Cost DoS | no `max_tokens`/rate/cost caps; unbounded agent loops | LLM10 | CWE-400/770 | : |
| `#AILLM-8_6` | Missing LLM Audit Logging | no LLM I/O trace (with PII masking) for incident response | : (OWASP Web A09 analog) | CWE-778 | : |
| `#AILLM-8_7` | Excessive Agency | agent/tool config without `disallowed_tools`/permission bounds; auto-approve of destructive tools; over-scoped credentials in tool defs | LLM06 | CWE-250 (assumed) | AML.T0110 |
| `#AILLM-8_8` | Vector & Embedding Weaknesses | RAG store without access control/tenant isolation; unvalidated embedding ingestion | LLM08 | CWE-284 (assumed) | AML.T0070 |
| `#AILLM-8_9` | AI Supply Chain | untrusted model artifacts (unsafe pickle/`torch.load`), unpinned model/dataset refs, unverified model hubs | LLM03 | CWE-502/494 · CWE-1357 | AML.T0010 |

Non-adopted OWASP LLM 2025 items and reason: LLM04 Data/Model Poisoning and LLM09 Misinformation are training-time/behavioral risks not statically assessable from a repository artifact (CTID P-5); do not tag them.

## 5. TA Tag Map (statically assessable subset : emit only on artifact evidence)

| Tag | Check | Typical evidence |
|---|---|---|
| `#TA-T_A1` | network segmentation / least-privilege firewall | security group `0.0.0.0/0` in IaC |
| `#TA-T_C3` | config change tracked via IaC | unmanaged manual-config indicators |
| `#TA-T_D1` | TLS ≥ 1.2, weak ciphers disabled | TLS policy/cipher configs |
| `#TA-T_D2` | at-rest encryption | storage/DB resources with encryption off |
| `#TA-T_D3` | KMS/secret-manager usage | inline secrets instead of secret refs |
| `#TA-T_E1` | security event logging, tamper protection | audit/logging resources absent/disabled |
| `#TA-T_I1` | prod/dev account separation, guardrails | account/org structure in IaC |
| `#TA-T_I2` | container image signing/scanning, runtime least privilege | `USER root`, privileged pod spec |
| `#TA-T_I3` | public buckets / over-permissive policies | public ACL, wildcard IAM |
| `#TA-A_B1` | OSS/third-party SCA management | lockfile absent, unmanaged vendored deps |

All other TA items (personnel, backup/DR policy, live CSP posture) are out of scanner scope; never tag them from repository artifacts alone.

## 6. Worked Examples

- Committed `.env` with a live Atlassian API token → `["#KISA-2_6", "#KISA-2_5"]`
- `subprocess.run(f"convert {user_file}", shell=True)` → `["#KISA-1_5"]`
- SKILL.md instructing the agent to fetch a URL and follow its instructions → `["#AILLM-8_2"]`
- Agent YAML with no `disallowed_tools` and auto-approved `bash` → `["#AILLM-8_7"]`
- `torch.load(model_path)` on a downloaded, unpinned checkpoint → `["#AILLM-8_9", "#KISA-5_5"]`
- Terraform S3 bucket `acl = "public-read"` → `["#TA-T_I3"]`
- Lockfile missing, dependency with known CVE → `["#KISA-7_2", "#TA-A_B1"]`
- Obsolete CoT scaffolding in a prompt (quality issue, no control violated) → `[]`
