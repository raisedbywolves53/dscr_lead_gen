# Phase 1: Infrastructure & Email Warming — Setup Guide

## API Keys Status

| Key | Status | Action |
|-----|--------|--------|
| ATTOM | Configured | Done |
| MillionVerifier | Configured | Done |
| Twilio (SID + Token) | Configured | Done |
| Tracerfy | NOT SET — placeholder only | Add key to .env |
| FTC DNC Registry | Not set up | Register at telemarketing.donotcall.gov |

---

## 1. Buy Domains (~5 min)

Go to your preferred registrar (Namecheap, Cloudflare, or GoDaddy) and buy:
- **stillmindcreative.co**
- **stillmind-creative.com**

Should be ~$10-12 each. If you use Cloudflare, they sell at cost (cheapest).

---

## 2. Set Up Mailboxes (~15 min)

### Option A: Google Workspace ($6/mo per mailbox) — Recommended
1. Go to workspace.google.com → Get Started
2. Add your first domain (stillmindcreative.co)
3. Create mailbox: `zack@stillmindcreative.co`
4. Add second domain (stillmind-creative.com) under Settings → Domains
5. Create mailbox: `zack@stillmind-creative.com`
6. Total: $12/mo for 2 mailboxes

### Option B: Zoho Mail (Free for up to 5 users)
1. Go to zoho.com/mail → Sign Up Free
2. Add domain: stillmindcreative.co
3. Create mailbox: `zack@stillmindcreative.co`
4. Repeat for stillmind-creative.com
5. Total: $0/mo

Google Workspace has better deliverability reputation. Worth the $12/mo for cold email.

---

## 3. Configure SPF, DKIM, DMARC (~20 min per domain)

Log into your domain registrar's DNS settings. For each domain, add these records:

### SPF (prevents spoofing)
- **Type:** TXT
- **Host:** @
- **Value (Google):** `v=spf1 include:_spf.google.com ~all`
- **Value (Zoho):** `v=spf1 include:zoho.com ~all`

### DKIM (email authentication)
- **Google:** Go to admin.google.com → Apps → Gmail → Authenticate Email → Generate DKIM key → Copy the TXT record → Add to DNS
- **Zoho:** Go to Zoho Mail admin → Email Authentication → DKIM → Add selector → Copy TXT record → Add to DNS

### DMARC (reporting)
- **Type:** TXT
- **Host:** _dmarc
- **Value:** `v=DMARC1; p=none; rua=mailto:zack@stillmindcreative.com`

After adding records, wait 15-30 min for DNS propagation. Verify at mail-tester.com by sending a test email.

---

## 4. Start Email Warmup (~10 min)

1. Go to instantly.ai → Sign up ($30/mo Starter plan)
2. Connect both new mailboxes:
   - Settings → Email Accounts → Add Account
   - Use IMAP/SMTP credentials from Google Workspace or Zoho
3. Enable warmup for both accounts:
   - Toggle "Warmup" ON for each account
   - Set daily warmup limit: start at 20/day, Instantly auto-increases
4. Let it run for **14-21 days** before sending any cold email
5. You'll see warmup stats (inbox rate, reply rate) in the dashboard

**While warming:** You can still send from zack@stillmindcreative.com (your real domain) for LinkedIn-originated conversations. The warmup only applies to the cold outreach domains.

---

## 5. Register for FTC DNC List (~10 min)

1. Go to telemarketing.donotcall.gov
2. Click "Register as a Seller/Telemarketer"
3. Create account with Still Mind Creative info
4. Select your first 5 area codes (free):
   - **919** (Wake County, NC)
   - **984** (Wake County, NC)
   - **216** (Cuyahoga County, OH)
   - **440** (Cuyahoga County, OH)
   - **317** (Marion County, IN)
5. Download the DNC files for these area codes
6. You must re-download every 31 days to stay compliant

---

## 6. Add Tracerfy API Key (~2 min)

1. Log into your Tracerfy account (tracerfy.com → Dashboard)
2. Find API key (usually under Settings or API section)
3. Add it to your .env file:
   - Open `C:\Users\USER\dscr_lead_gen\.env`
   - Find the commented-out Tracerfy line
   - Uncomment and paste your key:
     ```
     TRACERFY_API_KEY=your_actual_key_here
     ```

---

## Checklist

| # | Task | Est. Time | Status |
|---|------|-----------|--------|
| 1 | Buy 2 lookalike domains | 5 min | [ ] |
| 2 | Set up mailboxes (Google Workspace or Zoho) | 15 min | [ ] |
| 3 | Configure SPF/DKIM/DMARC for both domains | 40 min | [ ] |
| 4 | Start email warmup (Instantly.ai) | 10 min | [ ] |
| 5 | Register FTC DNC (5 area codes free) | 10 min | [ ] |
| 6 | Add Tracerfy API key to .env | 2 min | [ ] |
| — | ATTOM API key | — | [x] |
| — | MillionVerifier key | — | [x] |
| — | Twilio key | — | [x] |

**Total active time:** ~1.5 hours
**Then:** 2-3 weeks of passive email warming before cold sends

**Phase 2 (data pipeline) can start in parallel immediately.** Tracerfy isn't needed until the skip trace step.
