# Action Items for Frank (Updated March 6, 2026)

## Status: Skip trace + phone validation COMPLETE

### What We Have Now
- **7,537 leads** in Palm Beach + Broward
- **3,143 phone numbers** (2,826 mobile, 269 landline, 48 VoIP)
- **2,592 email addresses** (not yet validated — MV credits ran out)
- **Tracerfy cost: $57.60** | **Twilio cost: $9.00** | **Total spent: $66.60**

### What's Blocking Launch
1. DNC scrub (legally required before ANY phone outreach)
2. Email validation (need more MillionVerifier credits)

---

## DO NOW

### A. ~~Get MillionVerifier API key~~ DONE — BUT NEED MORE CREDITS
Your 2,000 credits are exhausted. Buy another batch to validate emails:
1. Log into https://millionverifier.com
2. Buy 5,000 credits for **$11.90** (covers all 2,592 emails with room to spare)
3. Credits never expire — no rush, but do before email campaigns

### B. ~~Get Twilio API keys~~ DONE
1,800 phone lookups completed. $6.00 remaining in trial.

### C. Register for FTC Do Not Call list (free — IN PROGRESS)
Register these **area codes** (not phone numbers):
- **561** (Palm Beach)
- **954** (Broward)
- **305** (Miami-Dade)
- **786** (Miami-Dade)

First 5 area codes are FREE. Once registered:
1. Download the DNC number files for those area codes
2. Save combined file as: `scrape/data/raw/dnc_list.csv` (one phone number per line)

### D. Decide: Tracerfy DNC scrub (~$57) vs free FTC only

| Option | Cost | Covers |
|--------|------|--------|
| FTC registry only | $0 | Federal DNC only |
| Tracerfy DNC scrub | ~$57 | Federal + State + DMA + TCPA litigators |

**Recommendation:** Spend the $57 on Tracerfy DNC. It catches TCPA litigators —
people who actively sue telemarketers. One lawsuit costs way more than $57.
Once you decide, tell me and I'll run it.

---

## DECISIONS (not urgent, but soon)

### E. Cancel Apollo.io ($99/mo)?
Apollo returned 0 usable contact data on all test leads. B2B database doesn't
cover private RE investors through LLCs. Tracerfy gave us 2,880 matches for $57.60.
**Recommendation: Cancel and save $99/mo.**

### F. Datazapp second-pass ($75 balance + $50 top-up)
Tracerfy missed ~3,557 leads. Datazapp uses a different database and may catch
some of those. Requires adding $50 to hit $125 minimum transaction.
**Not urgent** — focus on the 3,143 matched leads first.

---

## COMPLIANCE (before any outreach)

### G. Florida Telemarketing License
Before ANY phone outreach at scale, verify CCM has:
- Florida Telemarketing Business License ($1,500/year from FDACS)
- Salesperson licenses ($50/year per person making calls)
- Surety bond ($50,000 face value)

If CCM already holds these through their corporate structure, you're covered.

Florida-specific rules (stricter than federal):
- Calling hours: 8 AM - 8 PM local time (not 9 PM like federal)
- Max 3 calls per 24 hours to same person/same subject
- Caller ID spoofing is CRIMINAL in Florida

---

## COST SUMMARY

| Item | Cost | Status |
|------|------|--------|
| Tracerfy skip trace (2,880 matches) | $57.60 | DONE |
| Twilio phone validation (1,800 lookups) | $9.00 | DONE |
| MillionVerifier (2,000 credits) | $4.90 | DONE (exhausted, need more) |
| MillionVerifier top-up (5,000 credits) | $11.90 | BUY NOW |
| FTC DNC registry (4 area codes) | $0 | IN PROGRESS |
| Tracerfy DNC scrub (~3,143 phones) | ~$63 | DECIDE |
| **Total spent** | **$71.50** | |
| **Total remaining to launch** | **$12-$75** | |
