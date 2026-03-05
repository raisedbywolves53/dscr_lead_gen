# What I Need From You

While I build scripts 11-16 and 20, here are 3 things only you can do.
Do them in order — #1 is the most important.

---

## 1. Datazapp Batch Skip Trace (~5 min, $0.75)

This is our best source for cell phones and personal emails.
Apollo confirmed useless for private RE investors (0% hit rate).

**Steps:**
1. Go to https://www.datazapp.com
2. Upload this file: `scrape/data/enriched/datazapp_upload.csv`
3. Select "Skip Trace" service
4. Pay $0.75 (25 records x $0.03 each)
5. Download the results CSV
6. Save it as: `scrape/data/enriched/datazapp_results.csv`

That's it. The merge script (05b) will pick it up automatically.

---

## 2. API Keys for Contact Validation (when you have time)

We need two keys added to `scrape/.env`:

### Twilio (phone validation)
- Sign up at https://www.twilio.com (free trial gives you $15 credit)
- Go to Console > Account Info
- Copy your **Account SID** and **Auth Token**
- Add to `scrape/.env`:
  ```
  TWILIO_ACCOUNT_SID=your_sid_here
  TWILIO_AUTH_TOKEN=your_token_here
  ```
- Cost: $0.005 per lookup = ~$0.13 for 25 leads

### MillionVerifier (email validation)
- Sign up at https://millionverifier.com
- Go to API section, copy your API key
- Add to `scrape/.env`:
  ```
  MILLIONVERIFIER_API_KEY=your_key_here
  ```
- Cost: $0.50 per 1,000 emails = ~$0.01 for 25 leads

These are NOT blocking — everything else runs without them.
Validation is the last step before campaign export.

---

## 3. (Optional) Manual People Search (~2 hours)

Only do this if Datazapp results are thin.

1. Open `scrape/data/enriched/research_tracker.xlsx`
2. For each of the 25 leads, click the TruePeopleSearch link
3. Find the right person, copy their phone and email
4. Paste into the yellow "FOUND: Phone" and "FOUND: Email" columns
5. Save the file

The merge script (05b) will pick up your manual entries too.

---

## Status While You Do This

I'm building in parallel:
- Script 14: Wealth signals (FEC donations, SunBiz reverse lookup)
- Script 12: FDOR SDF purchase history
- Script 11: County clerk financing intelligence (research phase)
- Script 13: HUD rent estimates
- Portfolio detail view from existing FDOR data

None of these depend on Datazapp or API keys.
