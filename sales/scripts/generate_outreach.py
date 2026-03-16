"""
Generate Personalized Outreach Messages
========================================

Reads the NC loan officer prospect CSV and generates personalized:
  1. LinkedIn connection request (< 300 chars)
  2. LinkedIn DM sequence (3 messages)
  3. Cold email sequence (3 emails)

Personalization is based on: name, title, company, city, tier.
Branch managers get a different angle than individual LOs.

Usage:
    python sales/scripts/generate_outreach.py
    python sales/scripts/generate_outreach.py --tier 1-Priority
    python sales/scripts/generate_outreach.py --limit 20

Output:
    sales/outreach/outreach_messages.csv  (paste-ready for each prospect)
"""

import argparse
import csv
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
PROSPECTS_CSV = PROJECT_DIR / "sales" / "prospects" / "nc_loan_officers.csv"
OUTPUT_DIR = PROJECT_DIR / "sales" / "outreach"
OUTPUT_CSV = OUTPUT_DIR / "outreach_messages.csv"


def is_branch_manager(title: str) -> bool:
    """Check if this person manages a branch or team."""
    t = title.lower()
    return any(k in t for k in [
        "branch manager", "branch leader", "branch sales",
        "area manager", "sales manager", "team lead",
        "president", "owner", "founder", "co-owner", "co-founder",
        "division president", "vp", "vice president",
        "producing branch",
    ])


def is_senior(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ["senior", "sr.", "sr "])


def get_city_label(city: str) -> str:
    """Return a market label for the city."""
    if not city or city.strip() == "":
        return "North Carolina"
    c = city.strip()
    raleigh_area = ["Raleigh", "Cary", "Wake Forest", "Clayton", "Durham",
                    "Chapel Hill", "Fuquay-Varina", "Graham", "Apex", "Holly Springs"]
    charlotte_area = ["Charlotte", "Huntersville", "Mooresville", "Matthews",
                      "Waxhaw", "Fort Mill", "Gastonia"]
    if c in raleigh_area:
        return "Raleigh"
    if c in charlotte_area:
        return "Charlotte"
    return c


def generate_linkedin_connection(first_name: str, city_label: str, is_mgr: bool) -> str:
    """Generate a LinkedIn connection request < 300 chars."""
    if is_mgr:
        return (
            f"Hey {first_name} — I build lead intelligence tools for mortgage teams. "
            f"We score NC investment property owners and deliver ranked dossiers with "
            f"verified contact data. Think it could be a solid pipeline channel for "
            f"your {city_label} team. Would love to connect."
        )
    else:
        return (
            f"Hey {first_name} — I built a system that identifies and scores NC "
            f"investment property owners, then delivers contact-ready dossiers with "
            f"verified phone, email, and financing intel. Could be a new pipeline "
            f"channel for you in {city_label}. Would love to connect."
        )


def generate_dm_sequence(first_name: str, company: str, city_label: str,
                         is_mgr: bool) -> list:
    """Generate 3 LinkedIn DMs."""
    if is_mgr:
        dm1 = (
            f"Thanks for connecting, {first_name}. Quick question — how does your "
            f"team at {company} currently source investment property leads? Mostly "
            f"realtor referrals and repeat clients, or do you have a dedicated "
            f"investor pipeline?"
        )
        dm2 = (
            f"Reason I ask — I built a system that pulls public property records "
            f"across NC, scores owners by investment signals (portfolio size, entity "
            f"structure, equity, acquisition pace), resolves LLCs back to real people, "
            f"and enriches with verified contact data. We identified 65,000+ Tier 1 "
            f"investor leads in Wake and Mecklenburg alone.\n\n"
            f"For branch managers, the interesting part is this becomes a lead channel "
            f"you can offer your LOs — something most shops can't provide. Happy to "
            f"show you a sample dossier if you're curious."
        )
        dm3 = (
            f"Here's what a typical output looks like — 3 demo profiles showing "
            f"property count, entity structure, scoring signals, and equity estimates. "
            f"The full version includes verified phone, email, mortgage history, and "
            f"wealth indicators.\n\n"
            f"I'm offering a pilot to a few NC originators — 100 fully enriched "
            f"investor dossiers for $500. If even one converts to a funded deal, "
            f"that's 6-25x ROI.\n\n"
            f"Worth a 15-min call this week to walk through it?"
        )
    else:
        dm1 = (
            f"Thanks for connecting, {first_name}. Quick question — when you're "
            f"sourcing borrowers for investment property deals, are you mostly "
            f"working referrals and repeat clients or actively prospecting for new "
            f"investor leads?"
        )
        dm2 = (
            f"Reason I ask — I built a system that pulls public property records "
            f"across NC, scores owners by investment activity (portfolio size, entity "
            f"type, equity position, acquisition velocity), resolves entities back "
            f"to real people, and enriches with verified contact data.\n\n"
            f"Ran it across the NC market — 65,000+ Tier 1 investor leads in Wake "
            f"and Mecklenburg alone. Happy to show you what a sample lead dossier "
            f"looks like — no pitch, just want your feedback as someone in the "
            f"{city_label} market."
        )
        dm3 = (
            f"Here's what a typical output looks like — 3 demo profiles showing "
            f"property count, entity structure, scoring signals, and equity estimates. "
            f"Full version includes verified phone, email, mortgage history, and "
            f"wealth indicators.\n\n"
            f"I'm offering a pilot to a handful of NC originators — 100 fully "
            f"enriched dossiers for $500. One funded deal from the list covers the "
            f"cost 6-25x over.\n\n"
            f"Want to hop on a 15-min call this week?"
        )
    return [dm1, dm2, dm3]


def generate_email_sequence(first_name: str, company: str, city_label: str,
                            is_mgr: bool) -> list:
    """Generate 3 cold emails [subject, body]."""
    if is_mgr:
        e1_subj = f"New lead channel for your {company} team?"
        e1_body = (
            f"Hi {first_name},\n\n"
            f"I used to run marketing for the largest mortgage origination team in "
            f"the US. One thing I saw constantly: LOs fighting over the same realtor "
            f"relationships and recycled property lists.\n\n"
            f"I built a different kind of lead channel — a system that scores "
            f"investment property owners in NC by real signals (portfolio size, entity "
            f"structure, equity, acquisition pace) and delivers contact-ready dossiers "
            f"with verified phone, email, and financing intel.\n\n"
            f"For branch managers, the value is a pipeline channel you can offer your "
            f"team that nobody else in {city_label} has. Would a sample dossier for "
            f"the {city_label} market be useful?\n\n"
            f"— Zack Lewis\n"
            f"Still Mind Creative"
        )
        e2_subj = f"Re: New lead channel for your {company} team?"
        e2_body = (
            f"Hi {first_name}, following up — I attached a sample of what the lead "
            f"dossiers look like.\n\n"
            f"3 demo investor profiles from NC showing the depth of intel on each "
            f"lead: property count, entity structure, equity estimates, refi signals. "
            f"Full version includes verified phone + email + mortgage history.\n\n"
            f"Happy to generate a small batch for {city_label} if you want to see "
            f"real leads your team could work. 15 min to walk through it?\n\n"
            f"— Zack"
        )
        e3_subj = "$500 to test it"
        e3_body = (
            f"Last note on this — I'm offering a pilot to the first few NC "
            f"originators: 100 fully enriched investor dossiers for $500. One "
            f"funded deal from the list covers it 6-25x over.\n\n"
            f"For a branch, that's a test run you can put in one LO's hands and "
            f"see what happens. After that, monthly subscriptions start at "
            f"$1,500/mo for 250 leads with ongoing refresh.\n\n"
            f"If timing isn't right, no worries. But if pipeline is ever a "
            f"constraint for your team, happy to chat.\n\n"
            f"— Zack Lewis\n"
            f"Still Mind Creative, LLC"
        )
    else:
        e1_subj = f"Quick question about your investor pipeline"
        e1_body = (
            f"Hi {first_name},\n\n"
            f"I used to run marketing for the largest mortgage origination team in "
            f"the US. One thing I saw constantly: loan officers spending time and "
            f"money on lead sources that are just recycled property records with no "
            f"real intelligence.\n\n"
            f"I built something different — a system that scores investment property "
            f"owners by actual signals (portfolio size, entity structure, equity, "
            f"out-of-state ownership) and delivers contact-ready dossiers with "
            f"verified phone and email.\n\n"
            f"Just deployed it in NC. Would a sample dossier for the {city_label} "
            f"market be useful to you?\n\n"
            f"— Zack Lewis\n"
            f"Still Mind Creative"
        )
        e2_subj = f"Re: Quick question about your investor pipeline"
        e2_body = (
            f"Hi {first_name}, following up — I attached a sample of what the lead "
            f"dossiers look like.\n\n"
            f"3 demo profiles from NC showing the depth of intel on each lead. "
            f"Full version includes verified phone + email + mortgage history.\n\n"
            f"Happy to generate a small batch for your specific market if you want "
            f"to see real leads. 15 min to walk through it?\n\n"
            f"— Zack"
        )
        e3_subj = "$500 to test it"
        e3_body = (
            f"Last note on this — I'm offering a pilot to the first few NC "
            f"originators: 100 fully enriched investor dossiers for $500. One "
            f"funded deal from the list covers the pilot 6-25x over.\n\n"
            f"After that, monthly subscriptions start at $1,500/mo for 250 leads "
            f"with ongoing refresh.\n\n"
            f"If timing isn't right, no worries at all. But if pipeline is ever a "
            f"constraint, happy to chat.\n\n"
            f"— Zack Lewis\n"
            f"Still Mind Creative, LLC"
        )
    return [
        [e1_subj, e1_body],
        [e2_subj, e2_body],
        [e3_subj, e3_body],
    ]


def main():
    parser = argparse.ArgumentParser(description="Generate personalized outreach")
    parser.add_argument("--tier", default=None, help="Filter by tier (e.g. 1-Priority)")
    parser.add_argument("--limit", type=int, default=None, help="Max prospects")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load prospects
    prospects = []
    with open(PROSPECTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Tier") == "3-Skip":
                continue
            if args.tier and row.get("Tier") != args.tier:
                continue
            prospects.append(row)

    if args.limit:
        prospects = prospects[:args.limit]

    print(f"Generating outreach for {len(prospects)} prospects...")

    # Generate messages
    output_rows = []
    for p in prospects:
        name = p["Name"].strip()
        first = name.split()[0] if name else "there"
        company = p.get("Company", "").strip()
        title = p.get("Title", "").strip()
        city = p.get("City", "").strip()
        email = p.get("Email", "").strip()
        phone = p.get("Phone", "").strip()
        tier = p.get("Tier", "")

        city_label = get_city_label(city)
        is_mgr = is_branch_manager(title)

        # LinkedIn
        conn_req = generate_linkedin_connection(first, city_label, is_mgr)
        dms = generate_dm_sequence(first, company, city_label, is_mgr)

        # Email (only if we have an email)
        emails = generate_email_sequence(first, company, city_label, is_mgr)

        output_rows.append({
            "Name": name,
            "Company": company,
            "Title": title,
            "City": city,
            "Email": email,
            "Phone": phone,
            "Tier": tier,
            "Is_Manager": "Y" if is_mgr else "N",
            "LI_Connection_Request": conn_req,
            "LI_DM_1": dms[0],
            "LI_DM_2": dms[1],
            "LI_DM_3": dms[2],
            "Email_1_Subject": emails[0][0],
            "Email_1_Body": emails[0][1],
            "Email_2_Subject": emails[1][0],
            "Email_2_Body": emails[1][1],
            "Email_3_Subject": emails[2][0],
            "Email_3_Body": emails[2][1],
        })

    # Write output
    fieldnames = list(output_rows[0].keys())
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} personalized outreach sets to:")
    print(f"  {OUTPUT_CSV}")

    # Stats
    mgr_count = sum(1 for r in output_rows if r["Is_Manager"] == "Y")
    has_email = sum(1 for r in output_rows if r["Email"])
    print(f"\n  Branch managers/leaders: {mgr_count}")
    print(f"  Individual LOs: {len(output_rows) - mgr_count}")
    print(f"  With email (ready for cold email): {has_email}")
    print(f"  LinkedIn only (no email): {len(output_rows) - has_email}")


if __name__ == "__main__":
    main()
