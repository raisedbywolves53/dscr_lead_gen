"""
Step 18: Generate Outreach Playbook
=====================================

Takes investor profiles from Step 17 and generates agent-facing outreach
playbooks using Claude API. Each playbook includes:

  1. Investment behavior summary (data-driven, not assumptions)
  2. Suggested approach angles (3-4 specific value propositions)
  3. Opening conversation script (grounded in portfolio data)
  4. Strategic suggestions (what the agent can offer this investor)

This step uses the Claude API to generate natural-language narratives
from structured data. Cost: ~$0.01-0.03 per lead (Haiku).

Input:  scrape/data/demo/investment_profiles_{market}.csv (from Step 17)
        scrape/data/demo/showcase_7ep_{market}.csv (property details)
        scrape/data/demo/professional_enrichment_{market}.csv (optional, from Step 09)
Output: scrape/data/demo/playbooks_{market}.json (per-investor playbooks)

Usage:
    python scripts/18_generate_playbook.py --market wake
    python scripts/18_generate_playbook.py --market wake --model haiku
    python scripts/18_generate_playbook.py --market wake --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import anthropic
except ImportError:
    anthropic = None

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEMO_DIR = DATA_DIR / "demo"

# Load .env
if load_dotenv:
    load_dotenv(PROJECT_DIR / ".env")
    root_env = PROJECT_DIR.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)

# Model mapping
MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}


def build_prompt(profile: dict, properties: pd.DataFrame, professional: dict = None) -> str:
    """
    Build the prompt for Claude to generate an outreach playbook.

    The prompt includes:
      - Investor profile data (from Step 17)
      - Property-level details (from ATTOM enrichment)
      - Professional context (from Step 09, if available)
    """

    # Build property summary
    prop_lines = []
    for _, row in properties.iterrows():
        addr = row.get("address", "")
        avm = row.get("attom_avm_value", "")
        rent = row.get("attom_rent_estimate", "")
        beds = row.get("attom_beds", "")
        sqft = row.get("attom_sqft", "")
        year = row.get("attom_year_built", row.get("attom_year_built_profile", ""))
        lender = row.get("attom_lender_name", "")
        loan = row.get("attom_loan_amount", "")
        permits = row.get("attom_permit_count", "0")
        last_sale = row.get("attom_last_sale_date", "")
        last_price = row.get("attom_last_sale_price", "")
        equity = row.get("derived_equity", "")
        cash = row.get("derived_cash_buyer", "")

        prop_lines.append(
            f"  - {addr}\n"
            f"    AVM: ${avm} | Rent: ${rent}/mo | {beds}BR/{sqft}sqft | Built: {year}\n"
            f"    Last Sale: {last_sale} for ${last_price} | Cash: {cash}\n"
            f"    Lender: {lender} | Loan: ${loan} | Equity: ${equity}\n"
            f"    Permits: {permits}"
        )

    property_text = "\n".join(prop_lines) if prop_lines else "  No detailed property data available."

    # Professional context
    prof_text = ""
    if professional:
        prof_text = f"""
PROFESSIONAL CONTEXT (from LinkedIn/public records):
  Title: {professional.get('title', 'Unknown')}
  Company: {professional.get('company', 'Unknown')}
  Industry: {professional.get('industry', 'Unknown')}
  LinkedIn: {professional.get('linkedin_url', 'N/A')}
"""

    prompt = f"""You are generating an outreach playbook for a real estate agent who wants to build a relationship with this investor. The playbook should help the agent approach this investor with genuine value — not a cold pitch.

IMPORTANT RULES:
- Write from the perspective of advising the agent, not the investor
- Ground EVERY suggestion in actual data from the portfolio below
- Never make assumptions about what the investor "doesn't know" — they may be highly sophisticated
- Focus on what the agent can OFFER: local market knowledge, deal flow, property management connections, off-market opportunities
- Be specific — reference actual neighborhoods, property types, and price points from the data
- The investor's transaction history tells you what they want — help the agent speak to that pattern
- Do NOT include any mortgage/lending information in the playbook (RESPA compliance — this is for agents, not LOs)

INVESTOR PROFILE:
  Name: {profile.get('investor_name', '')}
  Properties: {profile.get('property_count', '')}
  Portfolio Value: ${profile.get('portfolio_total_value', '')}
  Investment Thesis: {profile.get('investment_thesis', '')}
  Price Range: {profile.get('price_range', '')}
  Price Preference: {profile.get('price_preference', '')}
  Avg Hold: {profile.get('avg_hold_years', '')} years
  Hold Strategy: {profile.get('hold_strategy', '')}
  Transactions/Year: {profile.get('transactions_per_year', '')}
  Days Since Last Purchase: {profile.get('days_since_last_purchase', '')}
  Predicted Next Purchase: {profile.get('predicted_next_purchase', '')}
  Financing: {profile.get('financing_pattern', '')} ({profile.get('cash_buyer_pct', 0)}% cash)
  Geographic Focus: {profile.get('geo_primary_city', '')} ({profile.get('geo_city_count', '')} cities)
  Concentrated: {profile.get('geo_concentrated', '')}
  Street Clustering: {profile.get('geo_street_clustering', '')}
  Monthly Rent (est): ${profile.get('total_monthly_rent', '')}
  Annual Rent (est): ${profile.get('total_annual_rent', '')}
  Total Equity: ${profile.get('total_equity', '')}
  Permits: {profile.get('total_permits', '')} (value: ${profile.get('total_permit_value', '')})
  Active Developer: {profile.get('active_developer', '')}
  Next Move: {profile.get('next_move_summary', '')}
  Thesis Signals: {profile.get('investment_thesis_signals', '')}
{prof_text}
PROPERTY PORTFOLIO:
{property_text}

Generate a JSON object with these exact keys:

{{
  "behavior_summary": "2-3 sentence summary of this investor's observable behavior pattern based on their transaction history, portfolio composition, and geographic focus. State only what the data shows.",

  "approach_angles": [
    {{
      "angle": "Short title of the approach",
      "rationale": "Why this approach fits based on portfolio data",
      "what_to_offer": "Specific value the agent brings"
    }}
  ],

  "opening_script": "A natural, conversational opening that references specific data points (neighborhood, property count, recent activity) to demonstrate the agent has done their homework. 2-3 sentences max. Should feel like a warm introduction, not a sales pitch.",

  "strategic_suggestions": [
    "Specific, actionable suggestion grounded in portfolio data"
  ],

  "conversation_starters": [
    "Questions the agent can ask that demonstrate market knowledge and invite the investor to share their strategy"
  ]
}}

Return ONLY the JSON object, no other text.
"""
    return prompt


def generate_playbook(client, profile: dict, properties: pd.DataFrame,
                      professional: dict = None, model: str = "haiku") -> dict:
    """Call Claude API to generate a playbook for one investor."""
    prompt = build_prompt(profile, properties, professional)
    model_id = MODEL_MAP.get(model, model)

    response = client.messages.create(
        model=model_id,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract text from response
    text = response.content[0].text.strip()

    # Parse JSON — handle markdown code blocks if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        playbook = json.loads(text)
    except json.JSONDecodeError:
        playbook = {"_raw_response": text, "_error": "Failed to parse JSON"}

    # Add metadata
    playbook["_investor_name"] = profile.get("investor_name", "")
    playbook["_model"] = model_id
    playbook["_input_tokens"] = response.usage.input_tokens
    playbook["_output_tokens"] = response.usage.output_tokens

    return playbook


def main():
    parser = argparse.ArgumentParser(
        description="Generate agent-facing outreach playbooks using Claude API"
    )
    parser.add_argument(
        "--market", type=str, required=True,
        help="Market to process: fl, wake"
    )
    parser.add_argument(
        "--model", type=str, default="haiku",
        choices=["haiku", "sonnet", "opus"],
        help="Claude model to use (default: haiku for cost efficiency)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print prompts without calling API"
    )
    parser.add_argument(
        "--investors", type=str, default="",
        help="Pipe-separated list of investor names to process (default: all)"
    )
    args = parser.parse_args()

    # Check dependencies
    if not anthropic:
        print("\n  ERROR: anthropic package not installed")
        print("  Run: pip install anthropic")
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key and not args.dry_run:
        print("\n  ERROR: ANTHROPIC_API_KEY not set")
        print("  Add ANTHROPIC_API_KEY=your_key to scrape/.env or export it")
        sys.exit(1)

    # Load data
    profiles_path = DEMO_DIR / f"investment_profiles_{args.market}.csv"
    properties_path = DEMO_DIR / f"showcase_7ep_{args.market}.csv"
    professional_path = DEMO_DIR / f"professional_enrichment_{args.market}.csv"

    if not profiles_path.exists():
        print(f"\n  ERROR: Profiles not found: {profiles_path}")
        print("  Run Step 17 first: python scripts/17_derive_investment_profile.py --market {args.market}")
        sys.exit(1)

    if not properties_path.exists():
        print(f"\n  ERROR: Properties not found: {properties_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  STEP 18: GENERATE OUTREACH PLAYBOOKS")
    print(f"  Market: {args.market.upper()}")
    print(f"  Model: {args.model} ({MODEL_MAP.get(args.model, args.model)})")
    print(f"{'='*60}")

    profiles_df = pd.read_csv(profiles_path, dtype=str)
    properties_df = pd.read_csv(properties_path, dtype=str)

    # Load professional enrichment if available
    professional_data = {}
    if professional_path.exists():
        prof_df = pd.read_csv(professional_path, dtype=str)
        for _, row in prof_df.iterrows():
            name = row.get("investor_name", "")
            professional_data[name] = row.to_dict()
        print(f"  Professional enrichment loaded: {len(professional_data)} investors")

    # Filter investors if specified
    if args.investors:
        investor_names = [n.strip() for n in args.investors.split("|")]
        profiles_df = profiles_df[profiles_df["investor_name"].isin(investor_names)]
        print(f"  Filtered to {len(profiles_df)} investors")

    print(f"  Investors to process: {len(profiles_df)}")

    # Initialize client
    client = None
    if not args.dry_run:
        client = anthropic.Anthropic(api_key=api_key)

    playbooks = []
    total_input_tokens = 0
    total_output_tokens = 0

    for _, profile_row in profiles_df.iterrows():
        investor_name = profile_row.get("investor_name", "")
        profile = profile_row.to_dict()

        # Get this investor's properties
        investor_props = properties_df[properties_df["owner_name"] == investor_name]

        # Get professional context if available
        professional = professional_data.get(investor_name)

        print(f"\n  Processing: {investor_name[:50]}")
        print(f"    Properties: {len(investor_props)}")
        print(f"    Professional context: {'Yes' if professional else 'No'}")

        if args.dry_run:
            prompt = build_prompt(profile, investor_props, professional)
            print(f"    Prompt length: {len(prompt)} chars")
            print(f"    --- PROMPT PREVIEW (first 500 chars) ---")
            print(f"    {prompt[:500]}")
            print(f"    --- END PREVIEW ---")
            continue

        playbook = generate_playbook(
            client, profile, investor_props,
            professional=professional, model=args.model
        )
        playbooks.append(playbook)

        in_tok = playbook.get("_input_tokens", 0)
        out_tok = playbook.get("_output_tokens", 0)
        total_input_tokens += in_tok
        total_output_tokens += out_tok

        print(f"    Tokens: {in_tok} in / {out_tok} out")

        if "_error" in playbook:
            print(f"    WARNING: {playbook['_error']}")
        else:
            summary = playbook.get("behavior_summary", "")[:100]
            angles = len(playbook.get("approach_angles", []))
            print(f"    Summary: {summary}...")
            print(f"    Approach angles: {angles}")

    if not args.dry_run and playbooks:
        # Save playbooks
        output_path = DEMO_DIR / f"playbooks_{args.market}.json"
        with open(output_path, "w") as f:
            json.dump(playbooks, f, indent=2)
        print(f"\n  Output saved: {output_path}")

        # Cost estimate
        # Haiku: $0.25/MTok input, $1.25/MTok output
        # Sonnet: $3/MTok input, $15/MTok output
        costs = {
            "haiku": (0.25, 1.25),
            "sonnet": (3.0, 15.0),
            "opus": (15.0, 75.0),
        }
        in_cost, out_cost = costs.get(args.model, (3.0, 15.0))
        total_cost = (total_input_tokens * in_cost + total_output_tokens * out_cost) / 1_000_000

        print(f"\n  {'='*60}")
        print(f"  PLAYBOOK GENERATION SUMMARY")
        print(f"  {'='*60}")
        print(f"  Investors processed: {len(playbooks)}")
        print(f"  Total input tokens:  {total_input_tokens:,}")
        print(f"  Total output tokens: {total_output_tokens:,}")
        print(f"  Estimated cost:      ${total_cost:.4f}")
        print(f"  {'='*60}")

    print(f"\n  Next step: Run build_tearsheets.py to create demo materials")
    print()


if __name__ == "__main__":
    main()
