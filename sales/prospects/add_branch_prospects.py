"""Add branch-sourced prospects to nc_loan_officers.csv"""
import pandas as pd
from pathlib import Path

CSV = Path(__file__).parent / "nc_loan_officers.csv"
df = pd.read_csv(CSV, dtype=str)
existing = set(df["Name"].str.lower().str.strip())
print(f"Existing: {len(df)} prospects")

cols = list(df.columns)
new = [
    # Fairway Independent Mortgage - Triangle branches
    ["Christie Latham","Fairway Independent Mortgage","Branch Sales Manager (Clayton)","Clayton","NC","","christieL@fairwaymc.com","(919) 649-3026","fairwayofthetriangle.org - NMLS #959118","1-Priority"],
    ["Don Waters","Fairway Independent Mortgage","Area Manager","Raleigh","NC","","thedonwatersteam@fairwaymc.com","(919) 795-5622","fairwayofthetriangle.org - NMLS #82361","1-Priority"],
    ["Natalya Hill","Fairway Independent Mortgage","Loan Officer","Clayton","NC","","natalya.hill@fairwaymc.com","(919) 614-0388","fairwayofthetriangle.org - NMLS #107187","2-Good"],
    ["Joe Pessolano","Fairway Independent Mortgage","Branch Sales Manager","Clayton","NC","","jpessolano@fairwaymc.com","(919) 395-0913","fairwayofthetriangle.org - NMLS #14120072","1-Priority"],
    ["Bart Poynor","Fairway Independent Mortgage","Loan Officer","Clayton","NC","","bartp@fairwaymc.com","(919) 235-7525","fairwayofthetriangle.org - NMLS #188427","2-Good"],
    ["April Woodard Cote","Fairway Independent Mortgage","Loan Officer","Clayton","NC","","april.cote@fairwaymc.com","(919) 262-6826","fairwayofthetriangle.org - NMLS #641077","2-Good"],
    ["Colin Tommerson","Fairway Independent Mortgage","Producing Branch Manager (Raleigh)","Raleigh","NC","","colin.tommerson@fairwaymc.com","(919) 395-0913","fairwayofthetriangle.org - NMLS #93404","1-Priority"],
    ["Lucas McClain","Fairway Independent Mortgage","Loan Officer","Raleigh","NC","","lucas.mcclain@fairwaymc.com","(919) 624-0953","fairwayofthetriangle.org - NMLS #1470439","2-Good"],
    ["Tee Cooper","Fairway Independent Mortgage","Branch Sales Manager (Graham)","Graham","NC","","tee.cooper@fairwaymc.com","(919) 909-6611","fairwayofthetriangle.org - NMLS #2075922","1-Priority"],
    ["Kim Blackwell","Fairway Independent Mortgage","Loan Officer","Wake Forest","NC","","kim.blackwell@fairwaymc.com","(919) 607-5827","fairwayofthetriangle.org - NMLS #2155054","2-Good"],
    ["Giovanny Salgado","Fairway Independent Mortgage","Loan Officer","Wake Forest","NC","","giovanny.salgado@fairwaymc.com","(203) 556-1872","fairwayofthetriangle.org - NMLS #400432","2-Good"],
    ["Stephanie Carroll","Fairway Independent Mortgage","Loan Officer","Clayton","NC","","stephanie.carroll@fairwaymc.com","(410) 458-5919","fairwayofthetriangle.org - NMLS #1639431","2-Good"],
    # CrossCountry Mortgage Raleigh 3529 (new names)
    ["Cedric Burke","CrossCountry Mortgage","SVP / Branch Leader","Raleigh","NC","","","(919) 632-8647","crosscountrymortgage.com - NMLS #119433","1-Priority"],
    ["Jayson Moore","CrossCountry Mortgage","Senior Loan Officer","Raleigh","NC","","","(919) 249-6392","crosscountrymortgage.com - NMLS #608397","2-Good"],
    ["Mark Reinhardt","CrossCountry Mortgage","Loan Officer","Raleigh","NC","","","(919) 604-7132","crosscountrymortgage.com - NMLS #2003989","2-Good"],
    ["Brandon Kelley","CrossCountry Mortgage","Loan Officer","Raleigh","NC","","","(919) 623-2115","crosscountrymortgage.com - NMLS #2052298","2-Good"],
    ["Susan Perez-Travers","CrossCountry Mortgage","Bilingual Loan Officer","Raleigh","NC","","","(919) 358-9503","crosscountrymortgage.com - NMLS #1294977","2-Good"],
    ["Patricia Acosta","CrossCountry Mortgage","Loan Officer","Raleigh","NC","","","(919) 949-3446","crosscountrymortgage.com - NMLS #1352203","2-Good"],
    ["Breandrea Hayes","CrossCountry Mortgage","Loan Officer","Raleigh","NC","","","(919) 699-3223","crosscountrymortgage.com - NMLS #737765","2-Good"],
    ["John Wilkerson","CrossCountry Mortgage","Senior Loan Officer","Raleigh","NC","","","(919) 285-6238","crosscountrymortgage.com - NMLS #1626884","2-Good"],
    # Towne Bank Mortgage Raleigh (full roster with emails)
    ["Cheryl Ellington","Towne Bank Mortgage","Mortgage Loan Officer","Raleigh","NC","","cheryl.ellington@townebankmortgage.com","(919) 412-9960","townebankmortgage.com - NMLS #71875","2-Good"],
    ["Christopher Coy","Towne Bank Mortgage","VP / Senior MLO","Raleigh","NC","","christopher.coy@townebankmortgage.com","(919) 306-8895","townebankmortgage.com - NMLS #1201896","1-Priority"],
    ["David Karg","Towne Bank Mortgage","Mortgage Loan Officer","Raleigh","NC","","David.Karg@townebankmortgage.com","(919) 534-7365","townebankmortgage.com - NMLS #664337","2-Good"],
    ["Doug Anderson","Towne Bank Mortgage","Senior MLO","Raleigh","NC","","doug.anderson@townebankmortgage.com","(919) 520-2005","townebankmortgage.com - NMLS #71843","1-Priority"],
    ["Kathryn Youngs","Towne Bank Mortgage","Mortgage Loan Officer","Raleigh","NC","","kathryn.youngs@townebankmortgage.com","(919) 796-3009","townebankmortgage.com - NMLS #118229","2-Good"],
    ["Lynn ONeal","Towne Bank Mortgage","Mortgage Sales Manager","Raleigh","NC","","lynn.oneal@townebankmortgage.com","(919) 201-3015","townebankmortgage.com - NMLS #69998","1-Priority"],
    ["Marisa Morgan","Towne Bank Mortgage","Mortgage Loan Officer","Raleigh","NC","","marisa.morgan@townebankmortgage.com","(239) 470-5012","townebankmortgage.com - NMLS #506530","2-Good"],
    ["Patrick OConnor","Towne Bank Mortgage","Mortgage Loan Officer","Raleigh","NC","","patrick.oconnor@townebankmortgage.com","(919) 606-6258","townebankmortgage.com - NMLS #65076","2-Good"],
    ["Phil Jawny","Towne Bank Mortgage","Senior Loan Officer (The Jawny Group)","Raleigh","NC","","Phil.Jawny@townebankmortgage.com","(919) 422-6035","townebankmortgage.com - NMLS #224037","1-Priority"],
    ["Trent Olson","Towne Bank Mortgage","VP / Senior MLO","Raleigh","NC","","Trent.Olson@townebankmortgage.com","(631) 655-6668","townebankmortgage.com - NMLS #741649","1-Priority"],
    ["Tyler Priest","Towne Bank Mortgage","Mortgage Loan Officer","Raleigh","NC","","Tyler.Priest@townebankmortgage.com","(919) 523-0925","townebankmortgage.com - NMLS #1483022","2-Good"],
    # Carolina Home Mortgage (full roster with emails)
    ["Kearny Davis","Carolina Home Mortgage","Loan Officer","Raleigh","NC","","Kearny@carolinahomemortgage.com","(919) 306-4840","carolinahomemortgage.com - NMLS #61383","2-Good"],
    ["Erica Sanders","Carolina Home Mortgage","Loan Officer","Raleigh","NC","","Erica@carolinahomemortgage.com","(919) 618-2420","carolinahomemortgage.com - NMLS #390083","2-Good"],
    ["Mindy Frailey","Carolina Home Mortgage","Loan Officer","Raleigh","NC","","Mindy@carolinahomemortgage.com","(910) 658-5189","carolinahomemortgage.com - NMLS #389553","2-Good"],
    ["Katie Evans","Carolina Home Mortgage","Loan Officer","Raleigh","NC","","Katie@carolinahomemortgage.com","(910) 728-0403","carolinahomemortgage.com - NMLS #101963","2-Good"],
    ["Linda Roberts","Carolina Home Mortgage","Loan Officer","Raleigh","NC","","Linda@carolinahomemortgage.com","(919) 306-1632","carolinahomemortgage.com - NMLS #48743","2-Good"],
    # Guild Mortgage Raleigh
    ["Lisa Brown","Guild Mortgage","Sales Manager","Raleigh","NC","","","(919) 649-1251","guildmortgage.com - NMLS #2103832","1-Priority"],
    ["Ruth Stephenson","Guild Mortgage","Area Manager","Raleigh","NC","","","(919) 946-8686","guildmortgage.com - NMLS #119289","1-Priority"],
    ["Sabrina Schell","Guild Mortgage","Loan Officer","Raleigh","NC","","","(919) 389-2349","guildmortgage.com - NMLS #98721","2-Good"],
    # Guaranteed Rate Raleigh
    ["Dave Mincy","Guaranteed Rate","Producing Branch Manager / VP","Raleigh","NC","","","(919) 442-4105","rate.com","1-Priority"],
    ["Fina Curtis","Guaranteed Rate","VP of Mortgage Lending","Raleigh","NC","","","(919) 442-4105","rate.com","1-Priority"],
    ["Carolyn Nelson","Guaranteed Rate","VP of Mortgage Lending","Raleigh","NC","","","","linkedin.com - NMLS #1179393","1-Priority"],
    # Certified Home Loans Raleigh
    ["Jeffrey Schneider","Certified Home Loans","Sr. MLO","Raleigh","NC","","jschneider@certifiedhomeloans.com","(919) 510-1108","chlraleigh.com - NMLS #70932","2-Good"],
    # Mutual of Omaha Raleigh
    ["Ryan Smith","Mutual of Omaha Mortgage","Loan Officer","Raleigh","NC","","","","mutualmortgage.com","2-Good"],
    ["Joe Spell","Mutual of Omaha Mortgage","Loan Officer","Raleigh","NC","","","","mutualmortgage.com","2-Good"],
    # Movement Mortgage Raleigh
    ["Kim Winters","Movement Mortgage","Team Lead Loan Officer","Raleigh","NC","","","(919) 535-4760","movement.com","1-Priority"],
    ["Tammi Rowe","Movement Mortgage","Loan Officer","Raleigh","NC","","","(919) 624-5550","movement.com","2-Good"],
    ["Pat Price","Movement Mortgage","Loan Officer","Raleigh","NC","","","(919) 535-4760","movement.com","2-Good"],
    # Atlantic Bay Raleigh
    ["Jeni Long","Atlantic Bay Mortgage","Mortgage Banker","Raleigh","NC","","","","raleighmba.org - NMLS #112538","2-Good"],
    # CrossCountry Raleigh 3510
    ["Corey Walker","CrossCountry Mortgage","Originating Branch Manager","Raleigh","NC","","","(330) 212-6410","crosscountrymortgage.com - NMLS #460704","1-Priority"],
]

added = 0
for row in new:
    name_lower = row[0].lower().strip()
    if name_lower not in existing:
        df.loc[len(df)] = dict(zip(cols, row))
        existing.add(name_lower)
        added += 1
    else:
        # Update existing entry if we have better data (email/phone)
        idx = df[df["Name"].str.lower().str.strip() == name_lower].index
        if len(idx) > 0:
            i = idx[0]
            if row[6] and (pd.isna(df.at[i, "Email"]) or df.at[i, "Email"] == ""):
                df.at[i, "Email"] = row[6]
            if row[7] and (pd.isna(df.at[i, "Phone"]) or df.at[i, "Phone"] == ""):
                df.at[i, "Phone"] = row[7]

df.to_csv(CSV, index=False)

t1 = len(df[df["Tier"] == "1-Priority"])
t2 = len(df[df["Tier"] == "2-Good"])
t3 = len(df[df["Tier"] == "3-Skip"])
has_email = (df["Email"].notna() & (df["Email"] != "")).sum()
has_phone = (df["Phone"].notna() & (df["Phone"] != "")).sum()

print(f"Added {added} new prospects")
print(f"Total: {len(df)} prospects")
print(f"Tier 1 (priority): {t1}")
print(f"Tier 2 (good): {t2}")
print(f"Tier 3 (skip): {t3}")
print(f"Actionable (T1+T2): {t1 + t2}")
print(f"With email: {has_email}")
print(f"With phone: {has_phone}")
