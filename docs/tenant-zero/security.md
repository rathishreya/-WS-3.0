# WS 3.0 — Information Security & Data Protection

**The complete security reference.** Written to be reviewable by a client's security team and to map cleanly onto SOC 2 / ISO 27001 / GDPR / regional audits. **Companions:** [`spec.md`](./spec.md) §8 (the SEC-1…14 data-trust requirements) · [`architecture.md`](./architecture.md) §7–§8 (technical enforcement). This doc is the *whole program*, not just the confidentiality model.

> **Design stance:** compliance-by-design, defense-in-depth, least-privilege, secure-by-default, and **cryptographic tenant isolation** (the operator *can't* read a customer, not "won't"). Where a specific product is interchangeable (which WAF, which KMS) we commit to the **requirement**, not the vendor.

**Conventions:** **IS-x** = an information-security requirement (this doc). **SEC-x** = the data-trust requirements in `spec.md` §8 (referenced, not repeated). `[V§n]` cites the vision.

---

## 1. Data classification (what we're protecting)

Everything is bucketed into five classes; handling rules follow the class.

| Class | Examples | At rest | In transit | Who/what may read |
|---|---|---|---|---|
| **C4 · Secret** | encryption keys, API/DB creds, salary/comp | HSM/KMS or field-encrypted (Fernet-class); never in code/logs | TLS 1.3 + mTLS | only the service that needs it, JIT |
| **C3 · Restricted content** | briefs, deliverables, files, PII | **not in the metadata DB** — tenant store, encrypted; processed only in the enclave | TLS 1.3, scoped links | the **tool** in the enclave, never a human `[V§2.1]` |
| **C2 · Confidential metadata** | the graph: names, volumes, relationships, statuses, file pointers, money events | control-plane DB, tenant-scoped, encrypted (BYOK on regional/sovereign) | TLS 1.3 | scoped by `(workspace_id, operating_entity_id)` + role |
| **C1 · Internal** | config, reference data, catalog | control-plane DB | TLS 1.3 | tenant admins/roles |
| **C0 · Public** | marketing, docs | — | TLS | anyone |

**IS-1** Every data element carries a class; controls are enforced by class, not by convention. **Content (C3) is never stored where metadata (C2) lives** — the single most important storage rule.

---

## 2. Data residency & storage — where EZ, McKinsey, and everyone's data actually sits

**The model, made authoritative.** Two planes, stored separately; isolation strength scales with the tenant's tier.

### 2.1 The two planes
- **Metadata plane (C2/C1):** the graph. Lives in the **control-plane Postgres**.
- **Content plane (C3):** the bytes. Lives in the **tenant's storage**, processed ephemerally in the **zero-retention enclave**. **Never** in the metadata DB — the DB holds only a `file_ref` pointer.

### 2.2 The isolation ladder (committed)
| Tier | Metadata storage | Keys | Content storage | Processing | Operator can read? |
|---|---|---|---|---|---|
| **Shared** | one Postgres cluster, **shared tables**, isolated by **Row-Level Security** on `(workspace_id, operating_entity_id)` | platform-managed | WS-managed object store, per-tenant bucket + per-tenant data key | WS regional enclave | yes (custodial) |
| **Regional** | region-pinned DB; **schema-per-tenant** for a harder wall | **BYOK** | tenant cloud (their S3/SharePoint) or WS regional | WS regional enclave | **no — cryptographic** |
| **Sovereign** | **dedicated database / instance** (their infra allowed) | **BYOK, HSM-backed** | **tenant's own infra, no egress** | **in-environment runtime, no egress** `[V§8]` | **no — cryptographic** |

**Decision (committed):** **RLS-pooled for Shared; dedicated DB + BYOK for Regional/Sovereign.** We do **not** create a table per tenant — it doesn't scale, complicates audit, and RLS + per-tenant keys give equal isolation on the shared tier.

### 2.3 Worked example — EZ (shared) alongside McKinsey (sovereign)
| Data | EZ · Tenant-Zero (shared) | McKinsey (sovereign) |
|---|---|---|
| Metadata / graph | shared cluster, shared tables, **RLS-isolated rows** | **dedicated DB**, McKinsey **BYOK** |
| Encryption key | platform-managed | **customer-managed — EZ cannot decrypt, incl. McKinsey's client list** |
| Content (files) | WS-managed S3, EZ bucket, EZ key | **McKinsey's own cloud / on-prem — never leaves** |
| Processing / AI | WS regional enclave | **in-McKinsey-environment, no egress** |
| Reporting | tenant-scoped read model | McKinsey-scoped, in their store |

**"Same server / different tables / different DB?"** — *two shared tenants share server, tables and DB (different **rows**, RLS-walled); a McKinsey-grade tenant gets a **different DB + own keys** (or own infra).*

### 2.4 Where **all** metadata sits (catalog)
- **Core graph** → control-plane Postgres (tier per §2.2).
- **Reporting / analytics** → separate read-model store, same tenant scope.
- **Audit log** → append-only, tamper-evident, tenant-inspectable, tenant scope.
- **Identity (`root_identity`)** → the **only** globally-central store — holds **login + portable reputation only, zero tenant content**. Skills/cost/relationships live in the tenant-scoped `person` membership, not here.
- **Content bytes** → never in any metadata store.

**IS-2** Residency is enforced physically: enclave, file-broker, and storage deploy **per region**; sovereign content never leaves the tenant environment. **IS-3** Two operating-entities in one org share a DB, isolated by `operating_entity_id` + RLS — unless split into their own workspace (then §2.2 applies).

---

## 3. Tenancy isolation controls

- **IS-4 · Row-Level Security** — every tenant-scoped query is constrained by `(workspace_id, operating_entity_id)` at the database layer; the app role **cannot** bypass it. Session scope is set per request by the gateway and never trusted from the client. *(Enforcement of SEC-6.)*
- **IS-5 · Per-tenant encryption** — each tenant's data is encrypted with a distinct key; **BYOK** on regional/sovereign means the platform holds no decryptable copy. *(SEC-8.)*
- **IS-6 · Envelope encryption** — data keys wrapped by a tenant master key in KMS/HSM; rotating the master re-wraps without re-encrypting data.
- **IS-7 · Isolation testing** — automated cross-tenant access tests (IDOR/row-leak) run in CI; a query that returns another tenant's row **fails the build**.

---

## 4. Identity & access management

- **IS-8 · AuthN** — OIDC; **MFA mandatory** for operator (L0) and workspace-admin roles, configurable-to-mandatory for others. Session tokens short-lived + rotated; refresh bound to device; idle + absolute timeouts.
- **IS-9 · Anti-abuse on auth** — lockout + credential-stuffing protection + rate limits on login/invite/reset (see §8).
- **IS-10 · AuthZ** — **server-authoritative** RBAC + POV-scoping at the gateway, over RLS at the data layer. No client-side permission checks. Every mutation re-checks role **and** row scope.
- **IS-11 · Scoped tenant-API credential** — JIT, least-privilege, **short-lived per-grant** tokens; never standing. A leaked token exposes **one file for minutes**, then expires; all grants revocable. *(SEC-7 — the crown-jewel surface.)*
- **IS-12 · Portable identity** — one global `root_identity`; per-workspace memberships; revoke SSO → that membership ends; the personal workspace is unreachable from any org. *(SEC-10/11/12.)*

---

## 5. Secrets & key management

- **IS-13** All secrets (DB creds, API keys, signing keys) live in a **secrets manager / vault** — **never** in source, config files, or CI logs. CI reads them at runtime via short-lived identities.
- **IS-14** Customer master keys in **KMS/HSM**; **BYOK lifecycle** supported: import, rotate, revoke. Revoking a tenant's key **renders their data unreadable** — the ultimate off-switch.
- **IS-15** Automatic rotation for platform secrets; documented rotation for BYOK; break-glass procedure logged to the tamper-evident audit.

---

## 6. Application security

- **IS-16 · OWASP baseline** — defenses for injection, XSS, CSRF, **SSRF**, insecure deserialization, and **broken access control (IDOR)**. Access control is the top risk here and is covered by IS-4/IS-7/IS-10.
- **IS-17 · Persisted GraphQL** — clients send **allowlisted query IDs only**, never arbitrary queries. This removes query-abuse, introspection leakage, and a whole DoS class at once.
- **IS-18 · Schema-validated I/O** — every payload validates against the JSON Schema (`architecture.md` Appendix A); `additionalProperties:false` rejects undeclared fields. Untrusted input is validated **and** treated as data, never as instructions.
- **IS-19 · SSRF/file safety** — file ingestion and any URL fetch run through an allowlisted, sandboxed fetcher (in the enclave); no access to internal metadata endpoints; MIME/size validated before pointer creation.
- **IS-20 · Output encoding** — contextual encoding everywhere untrusted data is rendered; strict CSP on the web app.

---

## 7. AI security (the composer reads untrusted content)

The AI composer reads a client's **brief and files** — untrusted input — to propose a plan. This is a live attack class (prompt injection, data exfiltration, poisoning). Controls:

- **IS-21 · Suggest-not-act** — the composer/allocator only **propose**; a human ratifies. An injected instruction ("assign to X, price $0, send data to Y") **cannot execute** — there is no action path without ratification. *(This is the primary control.)*
- **IS-22 · Scoped & stateless** — the composer sees **only this tenant's config**, runs in the zero-retention enclave, retains nothing, and has **no standing tool/credential access** — so there is nothing to exfiltrate to and no cross-tenant reach. *(SEC-13.)*
- **IS-23 · Input as data** — brief/file content is never concatenated into a trusted instruction context; the composer's system context and the untrusted content are separated.
- **IS-24 · Output validation** — the proposal must validate against the schema and reference only existing tenant config (offerings, people, rates); anything out-of-catalog is surfaced as a clarifying question, not executed.
- **IS-25 · No cross-tenant training** — prohibited; any future training is consent-tiered and sovereignty tenants are excluded by design. *(SEC-13.)*

---

## 8. Network, perimeter & automated-abuse (bot / DDoS) defense

Assume **active attack** — bots, credential stuffing, scraping, volumetric DDoS.

- **IS-26 · Edge WAF + DDoS protection** — managed WAF and volumetric/L7 DDoS mitigation in front of every public endpoint.
- **IS-27 · Bot management** — behavioral bot detection + challenge (CAPTCHA/JS challenge) on the **public-facing endpoints that bots target**: requester intake, invite acceptance, login, password reset, client/vendor portals.
- **IS-28 · Layered rate limiting** — token-bucket limits **per IP, per tenant, per endpoint, per credential**; expensive operations (compose, exports) throttled hardest; automatic backoff + temporary blocks on abuse.
- **IS-29 · Query-abuse killed by design** — persisted GraphQL (IS-17) means no arbitrary/expensive queries can be sent at all.
- **IS-30 · Network segmentation** — enclave, file-broker, channel-gateway are isolated segments; **enclave egress is locked** (no outbound), so even a full compromise has **no exfiltration path**; service-to-service over **mTLS** on private networking; the DB is never public.
- **IS-31 · Blast-radius limits** — short-lived scoped credentials (IS-11) + BYOK (IS-14) mean a breach of one surface can't cascade into cross-tenant data.
- **IS-32 · Abuse telemetry** — bot/DDoS signals feed the SIEM (§9) for auto-mitigation and alerting.

---

## 9. Logging, monitoring & detection

- **IS-33 · Tamper-evident audit** — append-only, **tenant-inspectable**, covering operator/admin actions ("don't-trust-us-verify"), every state change, and every money event. *(SEC-9.)*
- **IS-34 · No content in logs** — C3 content and C4 secrets are **never** logged; no human debugging on raw tenant data. *(SEC-4.)*
- **IS-35 · SIEM + anomaly detection** — centralized security logging with alerting on the crown-jewel surfaces: credential minting/use, cross-tenant access attempts (blocked by RLS but alerted), auth anomalies, egress attempts from the enclave, privilege changes.
- **IS-36 · Time-boxed detection goals** — alert on anomalous access in minutes, not days; monthly review of operator actions.

---

## 10. Data lifecycle, backup & disaster recovery

- **IS-37 · Retention** — content retention is tenant-configurable and minimized; the enclave retains **nothing**; metadata retained per policy + legal hold.
- **IS-38 · Right-to-erasure** — a tenant/subject deletion request purges content and tombstones metadata; on BYOK, key destruction is an instant crypto-erase.
- **IS-39 · Backups** — encrypted (tenant key), **per-region** (never crossing residency), with **tested restores**. Backups inherit the tenant's isolation and keys — a backup of a BYOK tenant is unreadable without their key.
- **IS-40 · DR** — targets: **RPO ≤ 15 min, RTO ≤ 4 h** (proposed); per-region failover; DR tested at least annually.

---

## 11. Third-party & supply-chain security

- **IS-41 · Vendor security** — each external dependency (WhatsApp/SMS providers, connectors, cloud) behind a reviewed adapter; least-privilege credentials; no tenant **content** passes to a channel provider — only mobilization metadata + one-tap payloads.
- **IS-42 · Supply chain** — dependency scanning + pinned versions + **SBOM**; signed builds; CI has no standing prod secrets. *(Directly answers the ERP's fragile-dependency lesson.)*
- **IS-43 · Cross-org boundary** — a partner workspace is an **opaque node**; brokered scoped file access (IS-11); provenance stripped per hop; a chained vendor stays invisible. *(SEC-1/§Layer-4.)*

---

## 12. Secure SDLC

- **IS-44** Mandatory code review; **security review** on changes touching auth, money, isolation, or the enclave.
- **IS-45** **Parity-test catalog** for money/lifecycle rules **before** the code (tested-money principle); isolation tests in CI (IS-7).
- **IS-46** Threat model maintained (§13); **penetration test pre-launch, on major changes, and at least annually**.

---

## 13. Threat model (asset → threat → control → residual)

| # | Asset | Threat | Primary control(s) | Residual |
|---|---|---|---|---|
| T1 | Tenant content (C3) | cross-tenant leak | RLS (IS-4) + per-tenant keys/BYOK (IS-5) + isolation tests (IS-7) | very low |
| T2 | Tenant content | **operator/insider** read | BYOK cryptographic lock (IS-14); no-human-bytes (SEC-4); tamper-evident audit (IS-33) | very low (sovereign: nil) |
| T3 | Scoped credential | token leak → data pull | JIT least-privilege, short-lived, revocable (IS-11) | low — one file, minutes |
| T4 | Public endpoints | **DDoS / volumetric** | edge WAF + DDoS (IS-26); rate limits (IS-28) | low |
| T5 | Auth / portals | **bot / credential stuffing / scraping** | bot mgmt + challenge (IS-27); lockout (IS-9); rate limits | low |
| T6 | AI composer | **prompt injection / exfiltration** | suggest-not-act (IS-21); scoped+stateless, no egress (IS-22); output validation (IS-24) | low |
| T7 | API | query-abuse / DoS / introspection | persisted GraphQL (IS-17) | very low |
| T8 | App | IDOR / broken access control | server-authoritative RBAC+RLS (IS-10/4); CI access tests (IS-7) | low |
| T9 | Content ingestion | **SSRF / malicious file** | sandboxed allowlisted fetch, MIME/size checks (IS-19) | low |
| T10 | Build/deps | **supply-chain compromise** | scanning + SBOM + signed builds (IS-42) | low |
| T11 | Backups | backup theft | encrypted with tenant key, residency-bound (IS-39) | very low |
| T12 | Cross-org edge | vendor sees client internals | encapsulation + provenance strip (IS-43) | low |
| T13 | Secrets | credential in code/logs | vault + no-content-in-logs (IS-13/34) | low |
| T14 | Enclave | compromise → exfil | egress-lock + segmentation (IS-30) | low — no path out |

---

## 14. Certification-readiness map

Design-to-pass now; certify later (an external audit + legal process, not a code artifact).

| Standard | Key control families | Where met | Gap to certify |
|---|---|---|---|
| **SOC 2 Type II** | access control, encryption, audit, monitoring, availability | IS-4/5/10/33/35, §10 | operating evidence over time; formal policies |
| **ISO 27001** | ISMS + Annex A controls | most of this doc | the **management-system wrapper** (policies, risk register, reviews) |
| **GDPR / DPA** | residency, minimization, erasure, DPA | §2, IS-37/38, control-plane-only | DPIA, processor agreements, records of processing |
| **India DPDP / UAE PDPL** | localization, consent | region-pinned + sovereign tiers (§2.2) | local counsel sign-off |
| **Sovereign (gov/PIF/financial)** | no-egress, customer keys | Sovereign tier, in-env runtime (§2.2) | per-client attestation |

**Honest line:** the **technical** controls that are hardest to retrofit — isolation, encryption, BYOK, audit, least-privilege, residency — are designed in from day one. The remaining work to certify is **program/process** (policies, evidence, DPIAs, pen-test reports, an ISMS), not architecture.

---

## 15. No-loose-ends coverage checklist

| Domain | Covered by |
|---|---|
| Tenant isolation (data leak) | IS-4/5/6/7 · SEC-6/8 |
| Insider / operator can't read | IS-14 · SEC-4/8/9 |
| Content confidentiality | §1–§2 · SEC-1/3 |
| Data residency (McKinsey case) | §2.2–§2.4 · IS-2 |
| Identity & access | IS-8…12 |
| Secrets & keys | IS-13/14/15 |
| App security (OWASP) | IS-16…20 |
| **AI / prompt injection** | IS-21…25 |
| **Bot / DDoS / abuse** | IS-26…32 |
| Monitoring & detection | IS-33…36 |
| Backup / DR / erasure | IS-37…40 |
| Supply chain / vendors | IS-41/42/43 |
| Secure SDLC / pen-test | IS-44/45/46 |
| Threat model | §13 |
| Compliance | §14 |

**If a client's security questionnaire asks it, it maps to a row above.** Anything not yet a row → raise it and it becomes one.

---

*The confidentiality requirements are in `spec.md` §8 (SEC-x); their technical enforcement is in `architecture.md` §7–§8; the full program is here. Flag any gap and it gets closed — nothing is left loose.*
