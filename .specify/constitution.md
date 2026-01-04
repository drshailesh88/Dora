# DocAssist Dora - Constitution

## Preamble

This constitution establishes the immutable principles governing the development of **Dora**, the DocAssist Medical Knowledge Platform. These articles are non-negotiable and must be enforced in every AI interaction, code review, and architectural decision.

---

## Article I: Privacy Sovereignty

All patient data SHALL be processed locally by default. No patient-identifiable information SHALL be transmitted to external services without explicit, informed consent from the physician. The system SHALL function fully offline for clinical data operations.

**Enforcement:** Every feature touching patient data MUST include privacy impact assessment.

---

## Article II: Physician Authority

All AI-generated content SHALL be presented in draft mode requiring explicit physician confirmation before persistence. The system SHALL never autonomously modify patient records, prescriptions, or clinical decisions. Human oversight is mandatory.

**Enforcement:** No `save()` or `persist()` operation without `physician_confirmed=True` flag.

---

## Article III: Evidence-Based Reasoning

All medical recommendations SHALL cite their sources with confidence scores. The system SHALL NOT generate medical advice without grounding in retrieved evidence. Hallucination prevention is a critical safety requirement.

**Enforcement:** Every response MUST include `sources: []` and `confidence: float` fields.

---

## Article IV: Regulatory Compliance

All features handling patient data SHALL comply with HIPAA (USA), DISHA (India), and GDPR (EU) requirements. Audit logging SHALL be enabled for all patient data access. Encryption at rest and in transit is mandatory.

**Enforcement:** Security review gate before any patient-facing feature deployment.

---

## Article V: Test-First Development

No feature SHALL be implemented without corresponding tests written first. Minimum 80% code coverage is required. Integration tests SHALL use real databases, not mocks, where feasible.

**Enforcement:** CI pipeline rejects PRs below coverage threshold.

---

## Article VI: Library-First Architecture

All features SHALL be implemented as reusable libraries before UI integration. CLI exposure is required for all core functionality. APIs precede interfaces.

**Enforcement:** No UI code without corresponding library implementation.

---

## Article VII: Simplicity

Maximum three projects per feature. No premature abstractions. Direct framework usage preferred over wrapper layers. If a solution requires more than three components, reconsider the approach.

**Enforcement:** Architecture review for any feature spanning >3 modules.

---

## Article VIII: Offline Resilience

The system SHALL provide core functionality without internet connectivity. Sync capabilities SHALL gracefully handle intermittent connectivity. Rural deployment is a first-class requirement.

**Enforcement:** All features tested in airplane mode.

---

## Article IX: Data Ownership

Physicians OWN their data. Export functionality in standard formats (JSON, CSV, FHIR) SHALL always be available. No vendor lock-in. No data monetization without explicit consent.

**Enforcement:** Export tests in every data-related feature.

---

## Article X: Zero Hidden Costs

No commission on patient payments. Transparent pricing. No surprise fees. Subscription model only.

**Enforcement:** Finance review for any revenue-related feature.

---

## Article XI: Accessibility

The system SHALL support Hindi, English, and major Indian regional languages. Voice control SHALL be available for hands-free operation. UI SHALL be usable in low-light clinical environments.

**Enforcement:** Accessibility audit before release.

---

## Article XII: Continuous Learning

The system SHALL support periodic knowledge base updates. Medical guidelines SHALL be refreshable without system downtime. Version control for medical content is required.

**Enforcement:** Update mechanism tests in knowledge pipeline.

---

## Ratification

This constitution is ratified upon project initialization and SHALL be referenced in every development session. Amendments require documented justification and explicit approval.

---

*Ratified: January 2026*
*Project: DocAssist Dora*
