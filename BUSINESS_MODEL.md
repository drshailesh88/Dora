# Dora Business Model & Go-To-Market Strategy

## The Core Concern Answered

**"If everything is offline, how do we make money?"**

**Short Answer:** Offline-first ≠ Free. It means the core functionality works without internet, but doctors still pay for:
1. **The knowledge itself** (medical content updates)
2. **Premium AI features** (Claude/GPT-4 when online)
3. **Ecosystem integration** (EMR, appointments, writing)
4. **Time-limited licensing** (subscription unlocks the offline capability)

**Think of it like Spotify:** You can download songs offline, but you still pay monthly. If you stop paying, downloaded songs stop working.

---

## Revenue Model

### Primary Revenue: Tiered Subscriptions (70% of revenue)

| Tier | Price | Target | Key Features |
|------|-------|--------|--------------|
| **FREE** | ₹0 | Trial users | 20 queries/month, basic textbooks, online-only, watermarked |
| **ESSENTIAL** | ₹499/month | GP, MBBS | Unlimited queries, offline mode, 5 textbooks, local LLM |
| **PROFESSIONAL** | ₹999/month | Specialists | Everything + voice agent, patient context, 20+ sources, Claude/GPT-4 |
| **CLINIC** | ₹2,499/month | Group practice | 5 doctors, shared knowledge, appointment integration, analytics |
| **ENTERPRISE** | Custom | Hospitals | Unlimited users, on-premise, custom content, API access |

**Why doctors will pay:**
- UpToDate costs ₹46,000/year ($559). We're 1/4th the price.
- HealthPlix charges ₹500-2000/month for just EMR. We include knowledge.
- Time saved = money earned. 10 queries/day × 2 mins saved = 6+ hours/month.

### Secondary Revenue: Transactional (20% of revenue)

| Service | Price | Margin | Volume |
|---------|-------|--------|--------|
| **SMS reminders** | ₹0.25/msg | 67% | High (appointments) |
| **WhatsApp notifications** | ₹0.20/msg | 67% | Medium |
| **Premium voice minutes** | ₹1/min | 50% | Growing |
| **PDF exports** (branded) | ₹5/export | 90% | Medium |
| **CME certificates** | ₹200/course | 80% | Low but growing |

### Tertiary Revenue: B2B & Partnerships (10% of revenue)

| Partner | Model | Example |
|---------|-------|---------|
| **Pharma companies** | Sponsored content (clearly labeled) | "Pfizer-sponsored diabetes guidelines" |
| **Medical publishers** | Revenue share | Harrison's digital rights |
| **Insurance companies** | Bulk licenses | Star Health provides Dora to network doctors |
| **Medical associations** | Group discounts | IMA members get 20% off |
| **Medical colleges** | Educational licenses | AIIMS students get free access |

---

## How Offline Still Makes Money

### The Licensing Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OFFLINE LICENSING ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   SUBSCRIPTION ACTIVE (₹999/month paid)                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  ✅ Local LLM works                                          │  │
│   │  ✅ Offline knowledge base accessible                        │  │
│   │  ✅ Voice agent active                                       │  │
│   │  ✅ Patient context available                                │  │
│   │  ✅ Monthly knowledge updates downloaded                     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              │ License check every 30 days           │
│                              │ (or on next internet connection)      │
│                              ▼                                       │
│   SUBSCRIPTION LAPSED (payment failed)                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  ⚠️  30-day grace period                                     │  │
│   │  ⚠️  "Renew subscription" prompts                            │  │
│   │  ⚠️  No new knowledge updates                                │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              │ After 30 days                         │
│                              ▼                                       │
│   SUBSCRIPTION EXPIRED                                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  ❌ App enters "read-only" mode                              │  │
│   │  ❌ No new queries (only view past queries)                  │  │
│   │  ❌ Voice agent disabled                                     │  │
│   │  ❌ Export your data (we don't hold hostage)                 │  │
│   │  ✅ EMR patient data remains yours (not locked)              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Technical Implementation

```python
# License verification (runs monthly or on connection)

class LicenseManager:
    def verify_subscription(self) -> bool:
        # 1. Check local license cache
        if self._is_license_valid_locally():
            return True

        # 2. If online, verify with server
        if self._is_online():
            license = self._fetch_license_from_server()
            self._cache_license_locally(license)
            return license.is_active

        # 3. If offline, use grace period
        if self._days_since_last_verification() < 30:
            return True

        # 4. Grace period expired
        return False

    def _on_subscription_expired(self):
        # Don't delete data - just limit functionality
        self.app.set_mode("read_only")
        self.app.show_renewal_prompt()
```

---

## Go-To-Market Strategy

### Why We Can Beat UpToDate

**UpToDate's Weaknesses (Our Opportunities):**

| UpToDate Weakness | Our Advantage |
|-------------------|---------------|
| ₹46,000/year ($559) | ₹11,988/year (₹999/mo) - **75% cheaper** |
| No Indian guidelines | **Native ICMR, NHM, state guidelines** |
| English only | **Hindi, Hinglish, regional languages** |
| Cloud-only | **Works in rural India without internet** |
| No patient context | **Integrated with your EMR** |
| No voice | **"Hey DocAssist" hands-free** |
| Separate from workflow | **Inside your EMR, appointments, prescriptions** |

### Target Market Segmentation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INDIAN DOCTOR MARKET (1.3M+)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   TIER 1: Early Adopters (Year 1 Focus)                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  • Young doctors (< 40 years) - 400K+                        │  │
│   │  • Specialists (cardiologists, diabetologists) - 100K+       │  │
│   │  • Doctors already using digital (EMR, telemedicine) - 200K+ │  │
│   │  • Private practitioners in Tier 2/3 cities - 300K+          │  │
│   │                                                               │  │
│   │  WHY: Tech-savvy, feel pain of expensive UpToDate,           │  │
│   │       value time-saving, willing to pay for tools            │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   TIER 2: Growth Market (Year 2-3)                                  │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  • Government hospital doctors - 200K+                       │  │
│   │  • Rural practitioners - 300K+                               │  │
│   │  • Medical students & residents - 100K+                      │  │
│   │                                                               │  │
│   │  WHY: Price-sensitive, need offline, want Indian context     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   TIER 3: Enterprise (Year 3+)                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  • Hospital chains (Apollo, Fortis, Max) - 50K+ doctors      │  │
│   │  • Medical colleges - 500+ institutions                      │  │
│   │  • Insurance networks - 100K+ empaneled doctors              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Sales Channels

| Channel | Cost | Conversion | Best For |
|---------|------|------------|----------|
| **1. Existing EMR users** | ₹0 | Very High | Launch base |
| **2. Medical conferences** | ₹50K/event | High | Specialists |
| **3. WhatsApp doctor groups** | ₹0 | Medium | Viral growth |
| **4. Medical associations** | ₹0-10K | High | Credibility |
| **5. Pharma partnerships** | Revenue share | Medium | Reach |
| **6. Medical reps** | Commission | Medium | Scale |
| **7. Digital ads** | ₹100-500/lead | Low | Awareness |
| **8. Referral program** | ₹500/referral | Very High | Organic |

### Launch Strategy (First 6 Months)

```
PHASE 1: Seed (Month 1-2)
├── Launch to existing DocAssist EMR users (FREE upgrade)
├── Get 50-100 beta users actively using
├── Collect feedback, fix bugs
├── Build testimonials and case studies
└── Goal: 100 active users, NPS > 50

PHASE 2: Credibility (Month 3-4)
├── Partner with 2-3 medical associations (IMA chapters)
├── Speak at 5 medical conferences
├── Get endorsements from 5 well-known doctors
├── Publish comparison: "Dora vs UpToDate"
├── Start paid subscriptions
└── Goal: 500 users, 100 paying, ₹1L MRR

PHASE 3: Growth (Month 5-6)
├── Launch referral program (₹500/referral)
├── WhatsApp marketing in doctor groups
├── Pharma partnership for sponsored guidelines
├── Medical college pilot (1 institution)
└── Goal: 2,000 users, 500 paying, ₹5L MRR
```

### Marketing Message

**For specialists (cardiologists, etc.):**
> "Stop paying ₹46,000/year for UpToDate. Get the same evidence-based answers for ₹999/month – plus it works offline and knows your patients."

**For GPs in Tier 2/3 cities:**
> "Medical knowledge that works without internet. Ask in Hindi. Get Indian guidelines. ₹499/month."

**For young doctors:**
> "The AI medical assistant your seniors wish they had. Voice-enabled, EMR-integrated, always updated."

---

## Financial Projections

### Year 1 Targets

| Metric | Q1 | Q2 | Q3 | Q4 | Year 1 |
|--------|----|----|----|----|--------|
| **Users (total)** | 500 | 2,000 | 5,000 | 10,000 | 10,000 |
| **Paying users** | 50 | 300 | 1,000 | 2,500 | 2,500 |
| **Conversion rate** | 10% | 15% | 20% | 25% | 25% |
| **ARPU** | ₹600 | ₹700 | ₹800 | ₹900 | ₹800 |
| **MRR** | ₹30K | ₹2.1L | ₹8L | ₹22.5L | ₹22.5L |
| **ARR** | ₹3.6L | ₹25.2L | ₹96L | ₹2.7Cr | ₹2.7Cr |

### Unit Economics

| Metric | Value | Notes |
|--------|-------|-------|
| **CAC** (Customer Acquisition Cost) | ₹2,000 | Blended across channels |
| **LTV** (Lifetime Value) | ₹14,400 | ₹800/mo × 18 months avg |
| **LTV:CAC Ratio** | 7.2:1 | Excellent (>3 is good) |
| **Payback Period** | 2.5 months | Quick payback |
| **Gross Margin** | 80% | SaaS-like margins |
| **Churn** | 5%/month | Target to reduce to 3% |

### Cost Structure (Monthly at 2,500 users)

| Cost Category | Amount | % of Revenue |
|---------------|--------|--------------|
| **Cloud infrastructure** | ₹2L | 9% |
| **LLM API costs** | ₹3L | 13% |
| **Content licensing** | ₹2L | 9% |
| **Support (2 people)** | ₹1L | 4% |
| **Marketing** | ₹5L | 22% |
| **Engineering (4 people)** | ₹6L | 27% |
| **Total Costs** | ₹19L | 84% |
| **Operating Profit** | ₹3.5L | 16% |

---

## Competitive Moats (Why We Win Long-Term)

### 1. Integration Moat
```
Dora ←→ DocAssist EMR ←→ Practice Manager ←→ Academic Writing

Patient books appointment → Doctor sees history → Dora suggests questions
→ Doctor queries Dora → Answer feeds into prescription → Bill generated

Competitors can't replicate this integrated experience.
```

### 2. Local-First Moat
- Offline capability is hard to build (local LLM, sync, licensing)
- Competitors are cloud-first; retrofitting is painful
- Rural India (40% of doctors) needs this

### 3. Indian Context Moat
- ICMR, NHM, state guidelines built-in
- Hindi/Hinglish support from day one
- Pricing for Indian market (not US pricing localized)

### 4. Data Moat (Over Time)
- We see what doctors ask (anonymized)
- We know treatment patterns
- We can personalize and improve
- This data is valuable to pharma, insurers, researchers

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **UpToDate drops price in India** | Medium | High | Our integration moat; they can't match offline |
| **Doctors don't pay** | Medium | Critical | Freemium proves value; EMR bundle |
| **LLM hallucinations harm patients** | Low | Critical | Draft mode; citations mandatory; disclaimers |
| **Content licensing issues** | Medium | Medium | Partner with publishers; create original content |
| **Big tech enters (Google, Microsoft)** | Low | High | Move fast; integration moat; niche focus |
| **Slow adoption** | Medium | Medium | Seed with EMR users; conference presence |

---

## Summary: How We Make Money

1. **Subscription fees** (₹499-2499/month) for:
   - Access to medical knowledge base
   - Monthly content updates
   - Offline capability license
   - Premium AI (Claude/GPT-4)
   - Voice agent

2. **Transactional revenue** from:
   - SMS/WhatsApp notifications
   - Branded exports
   - CME courses

3. **B2B partnerships** with:
   - Pharma (sponsored content)
   - Publishers (revenue share)
   - Insurers (bulk licenses)

**The key insight:** Doctors pay for TIME and CONFIDENCE.
- Time saved looking things up = more patients seen
- Confidence in treatment decisions = better outcomes, less liability

We're not selling software. We're selling **peace of mind** and **productivity**.

---

*Document Version: 1.0*
*Created: January 2026*
*For: DocAssist Dora Business Planning*

## Sources

- [UpToDate Subscription Costs](https://www.wolterskluwer.com/en/solutions/uptodate/subscribe)
- [Healthcare SaaS India - Inc42](https://inc42.com/buzz/healthcare-saas-grow-fastest-healthtech-45-cagr/)
- [India Digital Health Market - Grand View Research](https://www.grandviewresearch.com/industry-analysis/india-digital-health-market-report)
- [Practo Business Model](https://startuptalky.com/practo-business-revenue-model/)
- [HealthPlix Technologies](https://growjo.com/company/HealthPlix_Technologies)
