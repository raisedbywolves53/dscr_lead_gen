# Verified Service Pricing (Fact-Checked March 2026)

Every cost below has been verified against the vendor's actual website.
Previous estimates in this project were WRONG for several services.

---

## Skip Trace / Contact Enrichment

### Tracerfy (tracerfy.com) — PRIMARY PROVIDER
- **Skip trace**: $0.02/lead (1 credit) — "Normal Trace"
- **Enhanced trace**: $0.30/lead (15 credits) — adds aliases, relatives, past addresses
- **DNC scrub**: $0.02/phone (1 credit) — Federal DNC, State DNC, DMA, TCPA litigators
- **Returns**: Up to 8 phone numbers + 5 emails per lead, mailing address
- **Minimums**: NONE documented. No minimum order, no monthly fees, no subscription.
- **No credit card required to start**
- **API access**: Bearer token auth, CSV upload, async processing
- **API rate limit**: Max 10 POST trace requests per 5 minutes
- **Processing time**: 30-60 minutes for ~1,000 records
- **Status**: NOT YET USED — need to create account and get API key

### Datazapp (datazapp.com) — SECONDARY (second-pass only)
- **Minimum fund**: $75 account balance
- **Minimum order**: $125 per transaction (regardless of match count)
- **Phone append**: $0.03/match (pay-as-you-go), $0.025 ($1K plan), $0.02 ($2K plan)
- **Email append**: $0.03/match (pay-as-you-go), $0.025 ($1K plan), $0.02 ($2K plan)
- **Phone scrub (DNC)**: $0.005/number — "NO minimum order" (UNVERIFIED at checkout)
- **Email verification**: $0.005/email — "NO minimum order" (UNVERIFIED at checkout)
- **CRITICAL**: The $125 minimum means small batches are terrible value.
  25 leads with 7 matches = $125 = $17.86/match. Do NOT use for small runs.
- **We have**: $75 balance loaded, $0 spent. Transaction was not completed.
- **Best use**: Second-pass on Tracerfy misses when you have 2,000+ leads.
  Add $50 to reach $125 minimum, upload all Tracerfy misses at once.
- **Status**: Account active, $75 balance untouched

### Apollo.io (apollo.io) — $99/mo Professional Plan
- **Credits**: 48,000/year (granted upfront), used for email reveals and exports
- **Mobile credits**: 100/month (only ~12 phone reveals at 8 credits each)
- **Export credits**: 2,000/month
- **Overage**: $0.20/credit after exhausting plan credits, minimum 250 purchase
- **API access**: Basic on Professional. Advanced API requires Custom/Enterprise.
- **Reality check**: Matched names for 17/17 leads but returned 0 contact data.
  Apollo is B2B-focused. Private RE investors through LLCs have no profiles.
  Phone reveals are extremely limited (12/month). Wrong tool for this population.
- **We have**: Active $99/mo subscription. API key configured.
- **Recommendation**: CANCEL unless web UI searches on person names yield results.

### Wiza (wiza.co)
- **Free plan**: 20 emails + 5 phone numbers/month
- **Starter**: $49/mo for 100 credits
- **Requires**: LinkedIn Sales Navigator subscription (separate cost)
- **Credits expire monthly**
- **Best use**: Supplemental LinkedIn-based lookups, not primary skip trace

---

## Validation Services

### MillionVerifier (millionverifier.com)
- **Minimum**: 2,000 credits for $4.90 ($0.00245/email) — NO subscription
- **Credits never expire**
- **API access included** with any credit purchase

### Twilio Lookup (twilio.com)
- **Line Type Intelligence**: $0.008/lookup (mobile vs landline vs VoIP)
- **Carrier lookup**: $0.005/lookup
- **Free trial**: $15 credit on signup (~1,875 lookups)
- **No minimum purchase**

---

## DNC Compliance

### Federal DNC Registry (FTC)
- **First 5 area codes**: FREE
- **Per area code**: $82/year
- **For our use**: 4 FL area codes (561, 954, 305, 786) = FREE
- **Process**: Register at telemarketing.donotcall.gov, download numbers, scrub

### Tracerfy DNC Scrub (more comprehensive)
- **Cost**: $0.02/phone (1 credit)
- **Covers**: Federal DNC + State DNC + DMA + TCPA litigator lists
- **Returns**: is_clean flag, phone_type, per-list flags (national_dnc, state_dnc, dma, litigator)
- **Advantage over FTC-only**: Catches TCPA litigators who actively sue telemarketers

### State of Florida DNC
- Florida has its own DNC list separate from federal
- Must comply with BOTH federal and state
- Tracerfy DNC scrub includes state DNC; FTC registry does NOT

### Free DNC Tools (federal only)
- **FreeDNCList.com**: Upload CSV, free for 1 file per session, $19.99/yr unlimited
- **EVS7.com**: Free DNC scrubber tool

---

## Cost Summary — Full PB/Broward Run (7,537 leads)

### Recommended Plan (Tracerfy primary)

| Service | What | Cost |
|---------|------|------|
| Tracerfy skip trace | 7,537 leads @ $0.02 | $150.74 |
| Tracerfy DNC scrub | ~3,500 matched phones @ $0.02 | ~$70 |
| MillionVerifier | Validate emails found | $4.90 |
| Twilio Lookup | Phone type detection | $0 (free $15 trial) |
| FTC DNC Registry | 4 FL area codes | $0 (free) |
| **TOTAL** | | **$225.64** |

### Monthly recurring after launch

| Item | Cost |
|------|------|
| All data sourcing (FDOR, SunBiz, DBPR, HUD, county clerk) | $0 |
| DNC scrub refresh (must re-scrub every 31 days) | $0 (FTC) or ~$70 (Tracerfy) |
| Apollo.io (CANCEL — returns nothing for this population) | $0 |
| **Total monthly** | **$0-$70** |

### Datazapp $75 balance strategy
- DO NOT use for small batches (< 2,000 leads)
- Save for second-pass on Tracerfy misses
- Add $50 to reach $125 minimum transaction
- Upload 2,000+ Tracerfy-missed leads at once
- Expected additional matches: different database catches different people
