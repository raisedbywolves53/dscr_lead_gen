# Action Items (Updated March 5, 2026)

---

## 1. DONE: Datazapp Phone Append ($75 spent)

Results: 7 matches out of 25 (4 cell, 3 landline, 0 email).
Balance remaining: ~$74 in your Datazapp account.

**Next steps with your Datazapp balance:**
- Run **Email Append** on the same 25 leads (~$0.75 from balance)
- Run **DNC Phone Scrub** on all phones we have (~$0.04 from balance)
- Save ~$73 remaining for the full county run (covers ~2,400 matches)

**Save the Datazapp results as:** `scrape/data/enriched/datazapp_results.csv`

---

## 2. Wiza Lookups (you have an account)

For the 17 leads where we have a person name, try Wiza:
- Free tier: 20 emails + 5 phones per month
- Search each person by name on LinkedIn
- Wiza can pull email + phone from LinkedIn profiles
- This is our best shot for email addresses on these investors

---

## 3. DNC Compliance (MANDATORY before any outreach)

We MUST scrub all phone numbers against the Do Not Call registry.
Fines are up to $51,744 PER CALL to a DNC number.

**Free option:**
1. Go to https://www.freednclist.com
2. Upload CSV with our phone numbers
3. Download scrubbed results (free for 1 file per session)

**Paid option (from your Datazapp balance):**
- Datazapp Phone Scrub: $0.005/number, NO minimum order
- Uses your existing $74 balance

**Federal DNC Registry (free for us):**
- First 5 area codes are FREE
- We only need 4: 561 (PB), 954 (Broward), 305 + 786 (Miami-Dade)
- Register at https://telemarketing.donotcall.gov

**Florida State DNC:**
- Florida has its own separate DNC list
- Must comply with BOTH federal and state

---

## 4. API Keys for Validation

### Twilio (phone validation — FREE to start)
- Sign up at https://www.twilio.com — free trial gives $15 credit
- $0.008/lookup for Line Type Intelligence (mobile vs landline vs VoIP)
- $15 credit covers ~1,875 lookups — more than enough
- Add to `scrape/.env`:
  ```
  TWILIO_ACCOUNT_SID=your_sid_here
  TWILIO_AUTH_TOKEN=your_token_here
  ```

### MillionVerifier (email validation — $4.90 minimum)
- Sign up at https://millionverifier.com
- Minimum purchase: 2,000 credits for $4.90 (credits never expire)
- Add to `scrape/.env`:
  ```
  MILLIONVERIFIER_API_KEY=your_key_here
  ```

---

## Corrected Pricing

See `VERIFIED_PRICING.md` for full fact-checked pricing on every service.
Previous cost estimates in this project were wrong. All costs are now verified
against actual vendor websites as of March 2026.
