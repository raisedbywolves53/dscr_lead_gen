# Compliance — DNC, TCPA & Telemarketing Rules

## This Is Not Optional

Violations carry **$500–$1,500 per call/text** penalties. The FTC can enforce fines up to **$51,744 per violation**.

---

## Federal Requirements (Apply Everywhere)

### TCPA (Telephone Consumer Protection Act)
- **Prior express written consent** required for autodialed/prerecorded calls to cell phones
- **Prior express consent** (verbal OK) for manual calls to cell phones
- No consent needed for manual calls to business lines
- Must honor do-not-call requests within 30 days

### FTC DNC Registry
- Scrub all phone numbers against the Federal DNC list **every 31 days**
- First 5 area codes: FREE
- Additional area codes: $82/year each
- Register at: telemarketing.donotcall.gov

### CAN-SPAM (Email)
- Include physical mailing address in every email
- Include clear unsubscribe mechanism
- Honest subject lines (no deception)
- Honor opt-outs within 10 business days

### HPPA — Homebuyers Privacy Protection Act (Effective March 2026)
- **Bans purchase and use of mortgage trigger leads** (credit bureau data)
- Exceptions: consumer opted in, existing lender relationship, firm offer of credit
- Our system uses property records and public data — fully compliant

---

## State-Specific Requirements

Each state has additional rules. Check `deployments/{state}/CONFIG.md` for state-specific compliance details.

### Florida (Reference — Strictest Major Market)

| Rule | Florida Requirement | Federal |
|------|-------------------|---------|
| Calling hours | **8 AM – 8 PM local** | 8 AM – 9 PM |
| Call frequency | **Max 3 calls per 24 hours** per person | No federal limit |
| Caller ID | Must display accurate number — blocking/spoofing = criminal | Spoofing prohibited |
| Autodialer consent | Written consent required even with existing relationship | Written consent for cell |
| State DNC list | Separate from federal, must also scrub | Federal only |
| Telemarketing license | **$1,500/year** (FDACS) | No federal license |
| Salesperson license | $50/year per person | N/A |
| Surety bond | $50,000 face value (~$500-1,500 premium) | N/A |
| B2B calls | Florida rules ALSO apply to B2B | More lenient federally |

### North Carolina
- Check `deployments/north_carolina/CONFIG.md` for NC-specific rules
- NC has its own state DNC list
- Different licensing requirements than FL

---

## Mandatory Pre-Outreach Steps

### Before Every Phone Call
1. Scrub against **Federal DNC** (every 31 days)
2. Scrub against **State DNC** (frequency varies by state)
3. Verify phone **line type** (mobile vs landline vs VoIP)
4. Check against known **TCPA litigator lists**
5. Check **internal DNC/opt-out list**
6. Verify calling hours for recipient's time zone

### Before Every Text Message
1. All phone scrubbing steps above, PLUS:
2. Must have **prior express written consent** for automated/bulk texting
3. Register through **10DLC Campaign Registry**
4. Include opt-out instructions in every message

### Before Every Email
1. Include physical mailing address
2. Include clear unsubscribe mechanism
3. Honest subject line
4. Honor opt-outs within 10 business days

---

## DNC Scrubbing Options

| Method | Coverage | Cost | Recommended |
|--------|----------|------|------------|
| FTC Registry | Federal only | Free (5 area codes) | Minimum requirement |
| Tracerfy DNC | Federal + State + DMA + TCPA litigators | $0.02/phone | Best comprehensive option |
| FreeDNCList.com | Federal only | Free (1 file/session) | Quick check |

---

## Record Retention

| Record Type | Retention |
|-------------|-----------|
| Consent records | 6 years minimum |
| DNC scrub logs | 6 years minimum |
| Call/text logs | 6 years minimum |
| Opt-out records | 6 years minimum |
| Lead source documentation | 6 years minimum |

---

## CRM Compliance Fields

The Airtable CRM tracks compliance per investor:

| Field | Purpose |
|-------|---------|
| DNC Status | Clear / Federal DNC / State DNC / Internal DNC / Litigator / Not Checked |
| Consent Status | No Consent / Verbal / Written / Revoked |
| Phone Type | Mobile / Landline / VoIP / Unknown |
| Last DNC Scrub Date | When phone was last scrubbed |

**Never call a lead without checking these fields first.**
