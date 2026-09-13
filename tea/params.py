"""
Design basis, price register, and financial conventions.

Every price carries a source, a date, and a confidence tag:
    "sourced"      - taken from a named published assessment or dataset
    "estimate"     - engineering estimate derived from sourced inputs
    "placeholder"  - NOT adequately sourced; range is wide and the result
                     must be checked against the sensitivity analysis

Prices are USD per metric tonne unless the name says otherwise.
"""

from dataclasses import dataclass, field


# ----------------------------------------------------------------------------
# Design basis (Brief Section 2 - fixed)
# ----------------------------------------------------------------------------

HOURS_PER_YEAR = 8000

FEED_KG_H = {
    "glycerol": 1000.0,
    "methanol": 112.5,
    "water": 62.5,
    "fame": 37.5,
    "soaps": 18.75,
    "salts": 18.75,
}

FEED_TPY = {k: v * HOURS_PER_YEAR / 1000.0 for k, v in FEED_KG_H.items()}
CRUDE_TPY = sum(FEED_TPY.values())          # 10,000 t/yr
GLYCEROL_TPY = FEED_TPY["glycerol"]         # 8,000 t/yr
METHANOL_TPY = FEED_TPY["methanol"]         # 900 t/yr
FAME_TPY = FEED_TPY["fame"]                 # 300 t/yr
SOAP_TPY = FEED_TPY["soaps"]                # 150 t/yr
SALT_TPY = FEED_TPY["salts"]                # 150 t/yr


@dataclass
class Price:
    """A price with an explicit uncertainty range and provenance."""
    base: float
    low: float
    high: float
    unit: str
    source: str
    date: str
    confidence: str  # sourced | estimate | placeholder
    note: str = ""

    def __post_init__(self):
        if not (self.low <= self.base <= self.high):
            raise ValueError(
                f"Price range inconsistent: low={self.low} base={self.base} "
                f"high={self.high} ({self.source})"
            )


# ----------------------------------------------------------------------------
# Glycerine price complex
#
# Argus assesses US glycerine in US cents/lb delivered (refined) or fob (crude),
# US Midwest. 1 cent/lb = 22.046 $/t. Four dated observations are used to set a
# mid-cycle base rather than anchoring on the current spot peak:
#
#   Date          USP veg 99.7%   Technical 99.5%   Crude 80%    Tech-Crude
#                  (c/lb)          (c/lb)            (c/lb)       spread $/t
#   06 Jan 2022   113-135         98-108            25-32        1,643
#   ~Jan 2024      40-47          32-38              7-9            595
#   01 Oct 2025    60-66          47-51             21-24           584
#   16 Apr 2026    75-80          68-70             17-19         1,124
#
# The refined-to-crude spread IS the purification business, and it has moved by
# a factor of ~2.8x across these four observations. Base case uses the median of
# the four, NOT the April 2026 spot.
# ----------------------------------------------------------------------------

CENTS_LB_TO_USD_T = 22.046

GLYCERINE_HISTORY = [
    # (label, date, usp_veg c/lb mid, technical c/lb mid, crude c/lb mid)
    ("Argus Glycerine sample report", "2022-01-06", 124.0, 103.0, 28.5),
    ("Argus Glycerine report (via Scribd)", "2024-01 (approx)", 43.5, 35.0, 8.0),
    ("Argus Glycerine sample report", "2025-10-01", 63.0, 49.0, 22.5),
    ("Argus Glycerine Issue 26-15", "2026-04-16", 77.5, 69.0, 18.0),
]

PRICES = {
    # --- Glycerine complex -------------------------------------------------
    "crude_glycerol": Price(
        base=400.0, low=176.0, high=630.0, unit="$/t crude (80% basis)",
        source="Argus Glycerine, US Midwest crude 80% fob, four dated assessments "
               "2022-01-06 / ~2024-01 / 2025-10-01 / 2026-04-16 (17-19 c/lb latest)",
        date="2026-04-16",
        confidence="sourced",
        note="Base is the approximate median of four dated observations (~18 c/lb). "
             "Low is the Jan-2024 trough (8 c/lb); high is the Jan-2022 peak "
             "(28.5 c/lb). Current spot (Apr 2026) is 17-19 c/lb = $375-419/t, "
             "i.e. near the LOW end even as refined sits near its high.",
    ),
    "technical_glycerine": Price(
        base=1250.0, low=772.0, high=2271.0, unit="$/t (99.5%)",
        source="Argus Glycerine, technical grade 99.5% bulk delivered US Midwest; "
               "Apr 2026 assessment 68-70 c/lb = $1,499-1,543/t",
        date="2026-04-16",
        confidence="sourced",
        note="Base $1,250/t is mid-cycle, deliberately BELOW the Apr-2026 spot of "
             "~$1,521/t, which Argus attributes to import disruption via the Strait "
             "of Hormuz and reduced Indonesian/Malaysian arrivals.",
    ),
    "usp_glycerine": Price(
        base=1530.0, low=959.0, high=2734.0, unit="$/t (99.7% USP)",
        source="Argus Glycerine, USP vegetable refined 99.7% bulk delivered US "
               "Midwest; Apr 2026 assessment 75-80 c/lb = $1,653-1,764/t",
        date="2026-04-16",
        confidence="sourced",
        note="Base set at technical base + $280/t, the median USP-technical premium "
             "across the four dated observations. NOTE: if the client's feedstock is "
             "tallow/UCO rather than vegetable, the applicable assessment is USP "
             "tallow, which runs 3-6 c/lb BELOW USP vegetable.",
    ),
    "feed_grade_glycerin": Price(
        base=525.0, low=350.0, high=683.0, unit="$/t (80-88% basis, low methanol)",
        source="Argus kosher crude 80% fob US Midwest 24-27 c/lb (2026-04-16); "
               "Fastmarkets EN-GLY-0004 kosher crude 80% fob US plant 26-31 c/lb "
               "(2026-07-28 corrected assessment)",
        date="2026-07-28",
        confidence="estimate",
        note="PARTLY INFERRED. The kosher-crude assessment is the closest traded "
             "proxy for a clean, low-methanol, consistent-spec crude sold into "
             "feed/food channels, but the kosher premium is a FEEDSTOCK-ORIGIN "
             "premium, not a methanol-spec premium. The true feed-grade premium for "
             "de-methanolised material is not separately assessed. Treat the "
             "premium over plain crude as the key uncertainty in route E1.",
    ),

    # --- Co-products and credits -------------------------------------------
    "methanol": Price(
        base=600.0, low=450.0, high=1414.0, unit="$/t",
        source="Methanex Non-Discounted Reference Price, US Gulf Coast, "
               "$4.25/gal = $1,414/t (Sep 2026); Argus US spot TX Gulf Coast barge "
               "155-158 c/USG = $515-525/t (Jun 2026)",
        date="2026-09-01",
        confidence="estimate",
        note="DELIBERATELY NOT THE POSTED PRICE. US posted contract ($1,414/t) and "
             "US spot ($515-525/t) diverged by ~2.7x in 2026, far beyond the usual "
             "contract discount. The credit here is an AVOIDED PURCHASE at the "
             "biodiesel plant, so base is set near spot plus logistics. The high "
             "case carries the full posted price. This spread is a named tornado "
             "variable.",
    ),
    "acid_oil_ffa": Price(
        base=900.0, low=600.0, high=1200.0, unit="$/t",
        source="Brown grease (FFA >=16%) $800-1,000/t, Energy Solutions "
               "Intelligence UCO market review Q1 2026; bracketed by USDA AMS "
               "yellow grease Minneapolis $51-67/cwt = $1,124-1,477/t and "
               "choice white grease $68-71/cwt = $1,499-1,565/t, wk ending "
               "2026-08-28",
        date="2026-08-28",
        confidence="estimate",
        note="Split soap fatty acids. Brown grease is the right analogue, NOT "
             "refined fatty acid ($2,249/t, IMARC Q2 2026) and not yellow "
             "grease. Unprocessed trap grease has historically carried a "
             "DISPOSAL cost of $0.25-1.00/gal, so confirm the acid oil clears "
             "spec before booking it as revenue at all.",
    ),
    "recovered_fame": Price(
        base=1400.0, low=1000.0, high=1700.0, unit="$/t",
        source="USDA AMS inedible packer bleachable tallow, Chicago delivered, "
               "$75.00/cwt = $1,653/t (wk ending 2026-08-28); distillers corn "
               "oil 71.0-77.5 c/lb = $1,565-1,709/t (2026-09-08); FAME ex-UCO "
               "fob Rotterdam $1,200-1,500/t (Q1 2026)",
        date="2026-09-08",
        confidence="estimate",
        note="Recovered FAME from the acidulation top phase, returned to the "
             "esterification step or sold. Discounted below the tallow and DCO "
             "assessments because material recovered from an acidulation "
             "decanter is contaminated and is not saleable B100. Spot B100 "
             "assessments are entirely paywalled and the USDA B100 series is "
             "currently UNQUOTED, so no direct benchmark exists.",
    ),
    "solid_waste_disposal": Price(
        base=80.0, low=55.0, high=110.0, unit="$/t (a COST, entered positive)",
        source="New York landfill tipping fees, non-hazardous industrial solid "
               "waste: DANC Rodman $50.00/short ton (CY2026); Fulton County "
               "$68.00 in-county / $77.00 out-of-county (eff. 2026-01-01); "
               "Ulster County $150.00 (eff. 2026-01-01). Converted at "
               "1.1023 short ton/t",
        date="2026-01-01",
        confidence="estimate",
        note="TWO MATERIAL CAVEATS. (1) Seneca Meadows, Waterloo NY - the "
             "nearest large landfill to a Finger Lakes site - prices industrial "
             "waste by WASTE PROFILE and does not publish a rate; its posted "
             "MSW rate is $100/ton. (2) Seneca Meadows prohibits free liquids "
             "above 20%, so a wet, soluble salt cake may require solidification "
             "at unquantified extra cost, or be refused. A site-specific quote "
             "against an actual salt-cake analysis is a Stage 2 action.",
    ),
    "salt_cake_k": Price(
        base=690.0, low=550.0, high=790.0, unit="$/t (POSITIVE = SOP credit)",
        source="Sulphate of potash (K2SO4): ~$730/t North America "
               "(Business Analytiq, Jul 2026); $787.49/t USA CIF (Procurement "
               "Resource, Jul 2026); $550-900/t FOB/CIF band (MAWEB, "
               "2026-07-15). NOTE: USDA publishes no national SOP series",
        date="2026-07",
        confidence="estimate",
        note="Only available if the biodiesel plant uses a POTASSIUM catalyst "
             "(KOH / potassium methoxide). Brief Section 2 flags the cation as a "
             "decision-relevant unknown. These are FERTILISER-GRADE prices; a "
             "co-product salt cake will not command them without meeting "
             "fertiliser specification.",
    ),

    # --- Purchased inputs ---------------------------------------------------
    "sulfuric_acid": Price(
        base=875.0, low=300.0, high=950.0, unit="$/t (93%, delivered)",
        source="Westchester County NY contract award RFB-WC-26173, sulphuric "
               "acid 93% in bulk, DELIVERED upstate New York, $6.07/gal; "
               "converted at SG 1.835 (6.945 kg/gal) = $874/t",
        date="2026-06-04",
        confidence="sourced",
        note="ANCHORED ON A NEW YORK DELIVERED CONTRACT, NOT AN INDEX. Published "
             "benchmarks for this commodity span $40-457/t (IndexBox Gulf spot "
             "$40-70/t; IMARC North America $166/t; ExpertMarketResearch US "
             "$295-345/t; Procurement Resource USA CIF $457/t) because they "
             "describe 1,000-10,000 t Gulf Coast lots. Tank-truck freight to "
             "the Finger Lakes dominates the delivered price at our 91 t/yr "
             "consumption. The low bound retains an index-like value to show "
             "the item is immaterial either way.",
    ),
    "caustic_soda": Price(
        base=740.0, low=460.0, high=900.0, unit="$/t (100% NaOH dry basis)",
        source="Argus Chlor-Alkali, fob USGC contract $655-690/dry short ton = "
               "$722-761/dry metric tonne NaOH (Apr 2026); fob USGC export spot "
               "$460-490/dmt (wk 21, ~2026-05-22)",
        date="2026-04",
        confidence="sourced",
        note="BASIS WARNING: US caustic is quoted per DRY tonne of 100% NaOH. "
             "The contract range equates to $361-381 per tonne of as-delivered "
             "50% liquor. Domestic contract is the right basis for a small "
             "inland buyer; export spot is the low bound.",
    ),
    "hydrogen": Price(
        base=9000.0, low=6000.0, high=12000.0, unit="$/t H2 ($9/kg base)",
        source="EIA Manufacturing Energy Consumption Survey 2018 via 'Today in "
               "Energy' 2024-04-09: chemicals subsector pays $6.18/MMBtu but "
               "small high-purity users (electrical equipment subsector) pay "
               "$86.19/MMBtu - a 14x premium; = ~$0.92/kg vs ~$11.59/kg at HHV. "
               "DOE Hydrogen Program Record 20007 (2020): tube trailer delivery "
               "+ dispensing $9.46/kg at 450 kg/day, $8.17/kg at 1,000 kg/day",
        date="2024-04-09",
        confidence="estimate",
        note="CRITICAL for route D1, and the reason the academic literature "
             "flatters it. At ~5,100 t/yr PG this site needs ~480 kg H2/day, "
             "landing EXACTLY in DOE's sub-500 kg/day tube-trailer bracket - "
             "the highest-price tier. Published glycerol-to-PG TEAs assume "
             "$1.10/kg (UPenn, 2013 basis), which is refinery-scale pipeline "
             "hydrogen and overstates the case by roughly 8x. No 2025-26 "
             "delivered transaction price for a small US Northeast user is "
             "public; all regional assessments are paywalled.",
    ),
    "activated_carbon": Price(
        base=1800.0, low=800.0, high=2500.0, unit="$/t",
        source="Wood-based powdered activated carbon, decolorisation grade "
               "(the relevant grade, not coconut GAC): $900-1,800/t fob "
               "(Hojee Q1 2026); $600-3,000/t fob China (Tanke Carbon Q2 2026); "
               "US regional assessment $2,302/t (Tanke Q2 2026); USA CIF "
               "$949.69/t (Procurement Resource, Jul 2026)",
        date="2026-07",
        confidence="estimate",
        note="Sources disagree ~2.4x on the US market. Import landed-cost "
             "adders: freight $75-200/t, US duty 4.8% (HS 3802.10), "
             "port/customs $500-1,500/container.",
    ),
    "propylene_glycol": Price(
        base=2000.0, low=1600.0, high=2800.0, unit="$/t",
        source="IndexBox US Propylene Glycol USP market report, contract range "
               "$1.20-1.80/lb USP and $0.85-1.25/lb industrial grade (2026)",
        date="2026-07-10",
        confidence="placeholder",
        note="LOW CONFIDENCE. IndexBox is a market-report aggregator, not a price "
             "reporting agency, and its own USP and world-spot figures are mutually "
             "inconsistent once units are reconciled. Range is wide on purpose. "
             "Immaterial to the conclusion: D1 fails by $50M+.",
    ),

    # --- Utilities ----------------------------------------------------------
    "natural_gas": Price(
        base=13.0, low=8.0, high=16.5, unit="$/MMBtu",
        source="EIA New York industrial natural gas price: $14.71/Mcf (Feb 2026), "
               "$16.27/Mcf (latest monthly in series); converted at 1.037 MMBtu/Mcf",
        date="2026-04-30",
        confidence="sourced",
        note="New York industrial retail gas is roughly 2.5-3x the US average "
             "($4.26-5.23/Mcf per EIA STEO Aug 2026). This penalises every "
             "evaporation- and distillation-heavy route and is a genuine siting "
             "disadvantage for this client.",
    ),
    "electricity": Price(
        base=0.098, low=0.086, high=0.128, unit="$/kWh",
        source="EIA Electric Power Monthly Table 5.6.A, New York industrial "
               "10.17 c/kWh (Jun 2026, vs 9.21 Jun 2025); NYSERDA monthly NY "
               "industrial 2026: Jan 12.8, Feb 10.9, Mar 8.7, Apr 8.6, May 9.6 "
               "- YTD average 10.1 c/kWh; CY2025 average 9.5 c/kWh",
        date="2026-06",
        confidence="sourced",
        note="All-in average (total bill divided by kWh, including demand "
             "charges and taxes), which is the correct basis for a TEA. The "
             "8.6-12.8 c/kWh seasonal envelope is wide enough to matter if the "
             "load were seasonal; this process runs base-load so the annual "
             "average applies. EIA flags 2025-26 values as preliminary.",
    ),
    "cooling_water": Price(
        base=0.030, low=0.020, high=0.050, unit="$/m3",
        source="Engineering estimate, standard TEA convention",
        date="2026-09",
        confidence="estimate",
    ),
    "wastewater": Price(
        base=3.50, low=1.50, high=8.00, unit="$/m3",
        source="Engineering estimate - industrial effluent with high COD",
        date="2026-09",
        confidence="estimate",
        note="Glycerol-bearing effluent is high-COD and surcharged by POTWs.",
    ),
    "freight_out": Price(
        base=80.0, low=50.0, high=180.0, unit="$/t product",
        source="Argus Glycerine (2026-04-16): truck USGC-to-east-coast 15-18 c/lb; "
               "rail ~7-8 c/lb. Regional Northeast delivery assumed much shorter.",
        date="2026-04-16",
        confidence="estimate",
        note="Argus refined assessments are DELIVERED; crude is FOB. Freight is "
             "therefore deducted explicitly from refined revenue so the comparison "
             "against the FOB crude baseline is like-for-like.",
    ),

    # --- Labour -------------------------------------------------------------
    "operator_burdened": Price(
        base=105000.0, low=85000.0, high=145000.0,
        unit="$/operator-year, fully burdened",
        source="BLS OEWS May 2025, SOC 51-8091 Chemical Plant and System "
               "Operators: New York State mean $69,740 (median $62,980, P10 "
               "$55,070, P90 $90,690); national mean $79,970. Burden multiplier "
               "from BLS ECEC Table 4, March 2026, manufacturing: total "
               "compensation $48.27/h on wages of $32.20/h = 1.50x",
        date="2026-03",
        confidence="estimate",
        note="$69,740 x 1.50 = $105k. The 1.50x multiplier covers paid leave "
             "(7.5%), supplemental pay (5.7%), insurance (9.6%), retirement "
             "(3.3%) and legally required benefits (7.3%) and NOTHING ELSE - "
             "supervision, training, PPE and plant overhead are charged "
             "separately in this model, so there is no double count. Two "
             "weaknesses: the NY estimate rests on only ~120 employed persons "
             "statewide and runs 16% below the national median, and the OEWS "
             "figures come from secondary sites citing BLS. High bound carries "
             "the national P90 burdened.",
    ),

    # --- Reference prices for Pass-1 gate arithmetic only -------------------
    # These do not enter any costed route; they are the sourced basis for the
    # one-line kills recorded in the gate table.
    "acetic_anhydride": Price(
        base=900.0, low=840.0, high=970.0, unit="$/t",
        source="ExpertMarketResearch US $890/t (Q2 2026), 2026 US range "
               "$870-940/t; IMARC North America $840/t (Jul 2026); "
               "businessanalytiq North America $970/t (Sep 2026); Intratec US "
               "export fob $870/t (Nov 2025)",
        date="2026-09",
        confidence="sourced",
        note="Good convergence across four independent sources.",
    ),
    "triacetin": Price(
        base=1300.0, low=1200.0, high=1400.0, unit="$/t",
        source="ChemAnalyst CFR Mexico $1,400/t (Feb 2026); Chemball fob "
               "Shanghai ~$1,200/t (quotation expired, issued 2024-07-25)",
        date="2026-02",
        confidence="placeholder",
        note="NO free US bulk assessment exists. Note the reflexivity: triacetin "
             "is made FROM glycerol, so its price partly tracks our own "
             "feedstock cost.",
    ),
    "epichlorohydrin": Price(
        base=1550.0, low=1350.0, high=2050.0, unit="$/t",
        source="Intratec US fob export $1,630/t (Nov 2025); Procurement "
               "Resource USA CIF $1,705.82/t (Jun 2026); IMARC North America "
               "$1,350/t (Aug 2026); Argus assessed China exw $1,902/t "
               "(2026-04-16)",
        date="2026-08",
        confidence="sourced",
        note="SunSirs reports Chinese capacity additions of ~140 kt in 2024 and "
             "~170 kt in 2025 against much slower demand growth, and a 46.9% "
             "intra-year price swing in 2025. Structurally oversupplied.",
    ),
    "glycerol_carbonate": Price(
        base=3200.0, low=3000.0, high=3500.0, unit="$/t",
        source="$3.50/kg assumed as selling price in two independent 2025/2026 "
               "TEAs (RSC Advances 2026 10.1039/D5RA09460G; ACS Omega 2025 "
               "10.1021/acsomega.5c06226); >$3.15/kg required for profitability "
               "(Case Studies in Chem. & Env. Eng. 2023, 8, 100465)",
        date="2026",
        confidence="estimate",
        note="Disregard the $450-850/t 'glycerol carbonate' listings on trade "
             "aggregators - those CAS numbers are plain glycerol (56-81-5), not "
             "glycerol carbonate (931-40-8).",
    ),
    "solketal": Price(
        base=3000.0, low=2400.0, high=6200.0, unit="$/t",
        source="~$3,000/t cited in Sustainable Chemistry 2021, 2(2), 17 "
               "(10.3390/suschem2020017); RMB 45,000/t (97%, China, Apr 2025) "
               "per Valuates/QYResearch = ~$6,200/t",
        date="2026",
        confidence="placeholder",
    ),
    "dha": Price(
        base=50000.0, low=20000.0, high=150000.0, unit="$/t",
        source="$150/kg reported 2015, cited in Ciriminna et al., ChemistryOpen "
               "2018 (PMC5838383), which itself warns that 'publicly available "
               "prices for DHA differ greatly'; current Chinese supplier list "
               "prices $20-50/kg (2025-26)",
        date="2026",
        confidence="placeholder",
        note="An 11-year-old academic citation at $150/kg against current "
             "Chinese bulk offers near $35/kg is a 4x discrepancy that cannot "
             "be resolved from public data. Immaterial - the route fails on "
             "market volume, not price.",
    ),
}


# ----------------------------------------------------------------------------
# Capital cost index
# ----------------------------------------------------------------------------

CEPCI = {
    2002: 395.6,
    # January 2010 = 532.9, the value Attarbachi et al. (2024) state explicitly
    # as the basis for their US Gulf Coast cost estimate. Used in preference to
    # the 2010 annual average of 550.8 because both capex bases in this study
    # are 2010-based and 532.9 is the figure one of them actually cites; it is
    # also the mildly conservative choice (higher escalation factor).
    2010: 532.9,
    2013: 567.3,
    2015: 556.8,
    2018: 603.1,
    2019: 607.5,
    2020: 596.2,
    2021: 708.0,
    2022: 816.0,
    2023: 797.9,
    2024: 800.0,
    2025: 810.4,   # June 2025 final, Chemical Engineering
    2026: 870.5,   # June 2026 preliminary, Chemical Engineering (all-time high)
}
CEPCI_CURRENT = CEPCI[2026]
CEPCI_SOURCE = (
    "Chemical Engineering Plant Cost Index, June 2026 preliminary = 870.5 "
    "(May 2026 final = 864.0; June 2025 final = 810.4), chemengonline.com, "
    "published 2026-08-24. Historical annual values are the conventional "
    "published annual averages."
)


# ----------------------------------------------------------------------------
# Financial conventions (Brief Section 6)
# ----------------------------------------------------------------------------

@dataclass
class Financials:
    discount_rate: float = 0.12
    project_life_years: int = 15
    construction_years: int = 2
    tax_rate: float = 0.26
    macrs_class: int = 5
    working_capital_frac_fci: float = 0.15
    salvage_frac_fci: float = 0.0

    # Fixed-opex factors, Peters/Timmerhaus & Turton convention
    maintenance_frac_fci: float = 0.045
    insurance_tax_frac_fci: float = 0.020
    supervision_frac_labor: float = 0.25
    overhead_frac_labor_maint: float = 0.60
    shifts_per_position: float = 4.8   # 24/7 coverage incl. relief

    # Capex factoring
    lang_factor: float = 4.0           # fluid-processing plant, Lang
    contingency_frac: float = 0.20
    owners_cost_frac: float = 0.08

    feed_transfer_price_convention: str = (
        "Crude glycerol is charged to every route at its A1 market netback "
        "(PRICES['crude_glycerol']). Route A1 therefore has zero margin BY "
        "CONSTRUCTION and is the explicit hurdle. A zero-feed-cost sensitivity "
        "is reported separately."
    )


FIN = Financials()

DISCOUNT_RATE_JUSTIFICATION = """
12% nominal, applied to a mid-size private biodiesel producer:
  - A chemical major's WACC is typically 7-9%; this client is smaller, privately
    held, and cannot diversify a single-asset project risk.
  - The revenue line is exposed to a violently cyclical commodity spread, and the
    feedstock supply is itself policy-dependent (RFS/RVO, blender's credit, LCFS),
    so project risk and feedstock risk are CORRELATED rather than independent.
  - 10-12% is the range the brief proposes; 12% is taken as the base and 10% is
    carried in the sensitivity.
"""

# MACRS GDS percentages (half-year convention)
MACRS = {
    5: [0.2000, 0.3200, 0.1920, 0.1152, 0.1152, 0.0576],
    7: [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446],
}
MACRS_NOTE = (
    "IRS asset class 28.0 (Manufacture of Chemicals and Allied Products) carries a "
    "5-year GDS recovery period, so 5-year MACRS is the base. Many TEA texts default "
    "to 7-year; that case is run as a check and moves NPV by well under the capex "
    "uncertainty band."
)

CAPEX_ACCURACY = "AACE Class 4 (-30% / +50%), factored estimate, CEPCI-escalated"

# ----------------------------------------------------------------------------
# Steam system
# ----------------------------------------------------------------------------

STEAM_SYSTEM_FACTOR = 1.30
STEAM_SYSTEM_SOURCE = (
    "US DOE Advanced Manufacturing Office, 'How to Calculate the True Cost of "
    "Steam', and DOE/EnergyStar 'Benchmark the Fuel Cost of Steam Generation'. "
    "Fuel cost of steam CF = a_F x (H_S - h_W) / 1000 / eta_B; TOTAL generation "
    "cost CG = CF x 1.30, where the 0.30 covers makeup water, boiler feedwater "
    "treatment, pumping, combustion air, blowdown, deaeration, emissions "
    "control and boiler maintenance. DOE notes the factor 'may be more in "
    "smaller facilities', so 1.30 is the conservative-low end for a plant this "
    "size. Applied on top of the fired-fuel cost everywhere steam is raised. "
    "Boiler maintenance is thereby marginally double-counted against the 4.5%-"
    "of-FCI maintenance factor; the overlap is small and errs against the "
    "project."
)

