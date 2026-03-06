# Action Items for Frank (Updated March 6, 2026)

## Status: Tracerfy skip trace COMPLETE — 2,880 leads with contact info

### Results Summary
- **7,537 leads uploaded** → 6,437 accepted by Tracerfy → **2,880 matched (45%)**
- **2,869 phone numbers** found (mobile + landline, labeled)
- **2,461 email addresses** found
- **Cost: $57.60** (charges per match, not per upload)
- Results saved: `data/enriched/tracerfy_results.csv`

---

## ~~1. GET A TRACERFY API KEY~~ ✅ DONE

API key configured, full run completed successfully.

---

## 2. REGISTER FOR FTC DO NOT CALL LIST (free) — DO THIS NOW

This is legally required before making any cold calls. Fines are up to $51,744 per call.

1. Go to https://telemarketing.donotcall.gov
2. Register as a telemarketer (or have CCM register if they haven't)
3. Request these area codes (first 5 are FREE):
   - 561 (Palm Beach)
   - 954 (Broward)
   - 305 (Miami-Dade)
   - 786 (Miami-Dade)
4. Download the DNC number files
5. Save combined file as: `scrape/data/raw/dnc_list.csv` (one phone number per line)

### Alternative: Use Tracerfy DNC scrub
- $0.02/phone, but covers Federal DNC + State DNC + DMA + TCPA litigator lists
- Run: `python scripts/08_tracerfy_skip_trace.py --dnc-only`
- More comprehensive than FTC-only, but costs ~$70-100 for our phone list

---

## 3. DECIDE ON TRACERFY DNC vs FREE FTC DNC

| Option | Cost | Covers |
|--------|------|--------|
| FTC registry only (free) | $0 | Federal DNC only |
| Tracerfy DNC scrub | ~$70-100 | Federal + State + DMA + TCPA litigators |

**Recommendation:** Use Tracerfy DNC for the first run ($70-100). It catches TCPA litigators
who actively sue telemarketers. One lawsuit costs more than the scrub.

To use free FTC only:
```bash
python scripts/08_tracerfy_skip_trace.py --skip-dnc
```

To use Tracerfy DNC (included by default):
```bash
python scripts/08_tracerfy_skip_trace.py
```

---

## 4. DECIDE ON APOLLO.IO ($99/mo)

Apollo returned 0 usable contact data on all 25 test leads. Their database is B2B-focused
and private RE investors through LLCs don't have profiles.

**Options:**
- **Cancel Apollo** — save $99/mo. Tracerfy covers skip tracing better for this population.
- **Keep 1 more month** — try searching the 17 resolved person names in the Apollo web UI
  (not LLC names). If still no results, cancel.

---

## 5. DATAZAPP $75 BALANCE (ready to use as second-pass)

Your $75 is sitting in Datazapp. Now that Tracerfy is done, this is the right time.

**Strategy:**
- Tracerfy missed ~3,557 leads (no phone or email found)
- Upload those misses to Datazapp — different database catches different people
- You'll need to add $50 to hit the $125 minimum transaction
- Upload all 3,557 misses at once to get value from the minimum

**Do NOT use Datazapp for:**
- Small batches (25-100 leads) — the $125 minimum makes it $1.25-5.00/lead
- DNC scrubbing — Tracerfy or FTC are better options

---

## 6. AFTER TRACERFY RESULTS (automated steps)

Once Tracerfy results are in, run these commands:

```bash
# Merge all enrichment sources
python scripts/05b_merge_enrichment.py

# Validate contacts (needs API keys — see step 7)
python scripts/06_validate_contacts.py --county merged

# Export campaign-ready lists
python scripts/07_export_campaign_ready.py --county merged
```

---

## 7. OPTIONAL: VALIDATION API KEYS

These improve data quality but aren't required to start outreach.

### MillionVerifier (email validation — $4.90)
- Sign up at https://millionverifier.com
- Buy minimum 2,000 credits for $4.90 (credits never expire)
- Add to `scrape/.env`:
  ```
  MILLIONVERIFIER_API_KEY=your_key_here
  ```

### Twilio (phone type detection — free $15 trial)
- Sign up at https://www.twilio.com (free trial gives $15 credit)
- $0.008/lookup — $15 covers ~1,875 lookups
- Add to `scrape/.env`:
  ```
  TWILIO_ACCOUNT_SID=your_sid_here
  TWILIO_AUTH_TOKEN=your_token_here
  ```

---

## 8. COMPLIANCE: FLORIDA TELEMARKETING LICENSE

Before ANY phone outreach at scale, verify CCM has:
- Florida Telemarketing Business License ($1,500/year from FDACS)
- Salesperson licenses ($50/year per person making calls)
- Surety bond ($50,000 face value)

If CCM already holds these through their corporate structure, you're covered.
If not, this is required by Florida law before making cold calls.

Florida-specific rules (stricter than federal):
- Calling hours: 8 AM - 8 PM local time (not 9 PM like federal)
- Max 3 calls per 24 hours to same person/same subject
- Caller ID spoofing is CRIMINAL in Florida
- B2B calls are also covered by these rules

---

## COST SUMMARY

| Item | Cost | Status |
|------|------|--------|
| Tracerfy skip trace (2,880 matches) | $57.60 | ✅ DONE |
| Tracerfy DNC scrub (~2,869 phones) | ~$57 | ⏳ Decide (FTC is free) |
| FTC DNC registry (4 area codes) | $0 | ⏳ REGISTER NOW |
| MillionVerifier (email validation) | $4.90 | Optional |
| Twilio (phone type detection) | $0 (free trial) | Optional |
| **Total spent so far** | **$57.60** | |
| **Total to full launch** | **$62.50-$120** | |
| Datazapp second-pass (saved) | $75 (already paid) + $50 | Optional |
| Apollo.io (consider cancelling) | $99/mo | Review |
