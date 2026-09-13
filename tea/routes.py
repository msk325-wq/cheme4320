"""
Route enumeration: Pass 1 gates and Pass 2 mass/energy balances.

All arithmetic is written out inline so a reviewer can reproduce any tonnage by
hand. Every route that involves wet chemistry carries the Section F side-stream
credits, because the brief is right that omitting them mis-ranks the field.
"""

from .model import Route, CapexItem, Stream
from .params import (
    CRUDE_TPY, GLYCEROL_TPY, METHANOL_TPY, FAME_TPY, SOAP_TPY, SALT_TPY,
    STEAM_SYSTEM_FACTOR,
)

# ----------------------------------------------------------------------------
# Shared front-end mass balance (acidulation -> phase split -> methanol recovery)
#
# Acidulation with H2SO4 does two jobs at once:
#   (a) splits soaps      2 RCOONa + H2SO4 -> 2 RCOOH + Na2SO4
#       Basis sodium oleate MW 304, oleic acid MW 282, H2SO4 MW 98, Na2SO4 MW 142
#   (b) neutralises residual free alkali   2 NaOH + H2SO4 -> Na2SO4 + 2 H2O
#
# The 1.5 wt% "salts / catalyst residue" line is assumed 60% free-alkali
# (NaOH-equivalent) and 40% already-neutral salt. This split is an ENGINEERING
# ASSUMPTION and is carried in the assumption register.
# ----------------------------------------------------------------------------

SOAP_MW, FFA_MW, H2SO4_MW, NA2SO4_MW, NAOH_MW = 304.0, 282.0, 98.0, 142.0, 80.0

FREE_ALKALI_FRACTION = 0.60
ALKALI_TPY = SALT_TPY * FREE_ALKALI_FRACTION              # 90 t/yr NaOH-equivalent
NEUTRAL_SALT_TPY = SALT_TPY * (1 - FREE_ALKALI_FRACTION)  # 60 t/yr

ACID_FOR_SOAP = SOAP_TPY * (H2SO4_MW / (2 * SOAP_MW))     # 150 * 0.1612 = 24.2 t/yr
ACID_FOR_ALKALI = ALKALI_TPY * (H2SO4_MW / (2 * NAOH_MW)) # 90 * 0.6125 = 55.1 t/yr
ACID_EXCESS = 1.15
H2SO4_TPY = (ACID_FOR_SOAP + ACID_FOR_ALKALI) * ACID_EXCESS   # ~91.3 t/yr

FFA_FROM_SOAP = SOAP_TPY * (2 * FFA_MW / (2 * SOAP_MW))       # 150 * 0.928 = 139.2
SALT_FROM_SOAP = SOAP_TPY * (NA2SO4_MW / (2 * SOAP_MW))       # 150 * 0.2336 = 35.0
SALT_FROM_ALKALI = ALKALI_TPY * (NA2SO4_MW / (2 * NAOH_MW))   # 90 * 0.8875 = 79.9

DRY_SALT_CAKE_TPY = SALT_FROM_SOAP + SALT_FROM_ALKALI + NEUTRAL_SALT_TPY  # ~175 t/yr
WET_SALT_CAKE_TPY = DRY_SALT_CAKE_TPY / 0.80    # 20% occluded organics/moisture

# Organic top phase: unconverted FAME plus split fatty acids, 90% recovered
ACID_OIL_TPY = (FAME_TPY + FFA_FROM_SOAP) * 0.90              # ~395 t/yr

# Methanol recovery, 95% of the 900 t/yr in the feed
METHANOL_RECOVERY = 0.95
METHANOL_RECOVERED_TPY = METHANOL_TPY * METHANOL_RECOVERY     # 855 t/yr

# ----------------------------------------------------------------------------
# Energy for the shared front end
# ----------------------------------------------------------------------------

BOILER_EFFICIENCY = 0.82
GJ_PER_MMBTU = 1.05506

# Methanol stripping column: sensible heat on the whole feed + latent on the
# methanol at reflux ratio 1, plus co-evaporated water.
_SENSIBLE_GJ = CRUDE_TPY * 2.4e-3 * 60          # 10,000 t * 2.4 kJ/kg.K * 60 K
_MEOH_LATENT_GJ = METHANOL_TPY * 1.100 * 2      # 1,100 MJ/t, reflux ratio 1
_WATER_CO_EVAP_GJ = 200 * 2.260                 # 200 t water carried over
MEOH_COLUMN_GJ = _SENSIBLE_GJ + _MEOH_LATENT_GJ + _WATER_CO_EVAP_GJ   # ~3,884 GJ/yr
MEOH_COLUMN_MMBTU = MEOH_COLUMN_GJ / GJ_PER_MMBTU / BOILER_EFFICIENCY

# Water removal. This feed is unusually DRY (5 wt% vs the 10-15% typical of
# crude glycerol), which is a real advantage - triple-effect evaporation.
WATER_TO_EVAPORATE_TPY = 500 + 30               # feed water + neutralisation water
EVAP_GJ = WATER_TO_EVAPORATE_TPY * 2.260 / 2.5  # triple effect, ~2.5 economy
EVAP_MMBTU = EVAP_GJ / GJ_PER_MMBTU / BOILER_EFFICIENCY

# ----------------------------------------------------------------------------
# Vacuum distillation + bleaching consumption factors
#
# Source: Phoenix Equipment Plant #125, a Lurgi-technology 50 t/d pharmaceutical
# glycerin refinery (commissioned 2002, shut down 2008, now dismantled and
# offered for resale). Published consumption data, per metric tonne of USP:
#     steam   2,200 lb @225 psi + 3,600 lb @150 psi + 860 lb @45 psi = 6,660 lb
#     cooling water 87,000 gal | electricity 30 kWh | activated carbon 8-10 lb
#     45% NaOH 7.5 lb | wastewater 390 gal | residue 310 lb
# Published yield block: of the glycerol fed, 92% leaves as >99.8% Glycerin I,
# 3% as 85-90% Glycerin II, 5% to residue.
#
# That this plant was built in 2002 and shut in 2008 - exactly across the
# biodiesel build-out that flooded the glycerine market - is itself a data point
# and is carried into the risk register.
# ----------------------------------------------------------------------------

STEAM_T_PER_T_PRODUCT = 6660 * 0.453592 / 1000.0   # 3.021 t steam / t product
STEAM_GJ_PER_T = 2.75                              # live steam, no condensate return
CW_M3_PER_T = 87000 * 0.0037854                    # 329.3 m3 / t product
ELEC_KWH_PER_T = 60.0                              # 30 kWh distillation + balance
CARBON_T_PER_T = 9.0 * 0.453592 / 1000.0           # 0.00408 t / t product
NAOH_T_PER_T = 7.5 * 0.453592 * 0.45 / 1000.0      # 45% solution -> 100% basis
WW_M3_PER_T = 390 * 0.0037854                      # 1.476 m3 / t product

LURGI_RECOVERY_TO_PRIME = 0.92
LURGI_TO_SECOND_CUT = 0.03
PRETREATMENT_GLYCEROL_LOSS = 0.02   # glycerol lost to acid oil and salt cake

# ----------------------------------------------------------------------------
# Capex bases
#
# Two published bases are used, and they disagree substantially. Both are
# carried explicitly rather than averaged silently, because the disagreement is
# itself the headline capex uncertainty.
#
#  [CAPEX-1] Attarbachi, T., Kingsley, M., Spallina, V., "Experimental Scale-Up
#            and Technoeconomic Assessment of Low-Grade Glycerol Purification
#            from Waste-Based Biorefinery", Ind. Eng. Chem. Res. 2024, 63,
#            4905-4917, doi 10.1021/acs.iecr.3c03868 (EU GLAMOUR project).
#            67 t/d crude glycerol (24,455 t/yr) -> 1,630 kg/h at 82 wt%
#            purity, 77% recovery, from a feed with >16 wt% ash. ISBL EUR
#            5.31M, OSBL 2.13M, EPC 1.86M, contingency 0.74M, total plant cost
#            EUR 10.05M, working capital 0.91M, total investment EUR 19.15M.
#            Cost basis stated as US GULF COAST, January 2010, CEPCI = 532.9 -
#            so NO location de-rating is required. Converted at 1.33 USD/EUR.
#            The authors note their capex runs HIGHER than comparable
#            literature because of greater design detail.
#
#  [CAPEX-2] Bansod, Y. et al., "Techno-economic assessment of biodiesel-
#            derived crude glycerol purification processes", RSC Sustainability
#            2025, doi 10.1039/D4SU00599F. Aspen Plus V12.1 + SuperPro,
#            factorial method, 2010 equipment prices escalated by CEPCI with a
#            1.21 UK location factor. Basis 1,000 kg/h crude glycerol - almost
#            exactly this project's scale.
#              Vacuum distillation (VDP): total installed cost USD 2.05M,
#              total fixed capital 4.44M, 96.91% purity, 94.99% recovery,
#              +$78.38/t profit, 18.2-year payback, ROI 5.48%.
#              Membrane (MBP): TFC 6.00M, 93.92%/86.20%, -$2.72M/yr.
#              Ion exchange (IEP): TFC 6.04M, 98.75%/99.00%, -$11.42M/yr.
#
# IMPORTANT LIMITATION, carried into the report: NO peer-reviewed, US-basis
# capital cost was located for a plant actually reaching 99.5% technical or
# 99.7% USP grade. Every published TEA stops between 82% and 98.75%. The
# polishing increment below is therefore an ENGINEERING ESTIMATE bridging the
# published 96.91% case to the 99.5% specification that carries the price.
# ----------------------------------------------------------------------------

USD_PER_EUR_2010 = 1.33
UK_LOCATION_FACTOR = 1.21

_GLAMOUR_ISBL_USD_2010 = 5.31e6 * USD_PER_EUR_2010          # $7.06M, USGC basis
_RSC_VDP_ISBL_USD_2010 = 2.05e6 / UK_LOCATION_FACTOR        # $1.69M, de-located
_RSC_BASIS_CRUDE_TPY = 8000.0     # 1,000 kg/h x 8,000 h/yr


def pretreatment_capex(crude_tpy=CRUDE_TPY):
    return CapexItem(
        name="Pretreatment: acidulation, settler, methanol recovery, "
             "filtration, evaporation",
        basis_cost=_GLAMOUR_ISBL_USD_2010,
        basis_capacity=24455.0,
        capacity=crude_tpy,
        exponent=0.60,
        cepci_year=2010,
        capacity_unit="t/yr crude glycerol fed",
        source="[CAPEX-1] Attarbachi et al., Ind. Eng. Chem. Res. 2024, 63, "
               "4905-4917, ISBL EUR 5.31M for 67 t/d; US Gulf Coast Jan-2010 "
               "basis, CEPCI 532.9, converted at 1.33 USD/EUR",
    )


def distillation_capex(crude_tpy):
    # Scaled on CRUDE fed rather than glycerol, because the column and the
    # ejector set are sized by total throughput. The Bansod basis processes
    # 1,000 kg/h of crude but yields only 392 kg/h of product, so its feed is
    # far dirtier than ours; scaling on product would understate the duty.
    return CapexItem(
        name="Vacuum distillation, steam ejectors, bleaching, residue still",
        basis_cost=_RSC_VDP_ISBL_USD_2010,
        basis_capacity=_RSC_BASIS_CRUDE_TPY,
        capacity=crude_tpy,
        exponent=0.60,
        cepci_year=2010,
        capacity_unit="t/yr crude glycerol to the distillation train",
        source="[CAPEX-2] Bansod et al., RSC Sustainability 2025 "
               "(10.1039/D4SU00599F), VDP total installed cost USD 2.05M @2010 "
               "at 1,000 kg/h crude, de-located from the UK 1.21 factor",
    )


def polishing_capex(crude_tpy):
    """Bridge from the published 96.91% vacuum-distillation case to the 99.5%
    technical specification that actually carries the refined price.

    This is the weakest link in the capex estimate and it is an engineering
    estimate, not a sourced figure, because no peer-reviewed US-basis capital
    cost exists for a plant reaching 99.5%+. Sized at 45% of the distillation
    ISBL, representing a second distillation stage, additional bleaching
    capacity and a polishing filter train.
    """
    return CapexItem(
        name="Polishing to 99.5%: second distillation stage, extended "
             "bleaching, polish filtration",
        basis_cost=_RSC_VDP_ISBL_USD_2010 * 0.45,
        basis_capacity=_RSC_BASIS_CRUDE_TPY,
        capacity=crude_tpy,
        exponent=0.60,
        cepci_year=2010,
        capacity_unit="t/yr crude glycerol to the distillation train",
        source="ENGINEERING ESTIMATE. No peer-reviewed US-basis capex was "
               "located for a glycerol plant reaching 99.5% or 99.7%; all "
               "published TEAs stop between 82% and 98.75% purity. Commercial "
               "plants at this grade exist (Argent Energy 50 kt/yr at 99.7%, "
               "Andreotti Impianti technology, technical grade from Dec 2023) "
               "but none discloses cost.",
    )


def ion_exchange_capex(crude_tpy):
    # Increment between the Bansod ion-exchange and vacuum-distillation cases,
    # plus QC laboratory and batch-documentation systems for cGMP.
    increment = (2.81e6 - 2.05e6) / UK_LOCATION_FACTOR
    return CapexItem(
        name="Ion exchange, polish bleaching, cGMP QC laboratory and "
             "documentation systems",
        basis_cost=increment + 0.55e6,
        basis_capacity=_RSC_BASIS_CRUDE_TPY,
        capacity=crude_tpy,
        exponent=0.60,
        cepci_year=2010,
        capacity_unit="t/yr crude glycerol to polishing",
        source="[CAPEX-2] Bansod et al. 2025, IEP-minus-VDP installed-cost "
               "increment (USD 0.76M @2010 UK basis), de-located, plus a "
               "USD 0.55M engineering estimate for cGMP quality infrastructure",
    )


def methanol_only_capex(crude_tpy=CRUDE_TPY):
    # Methanol recovery is roughly one fifth of the pretreatment ISBL (the
    # column, condenser, receiver and controls), plus dedicated tankage and
    # truck loading for the de-methanolised product.
    return CapexItem(
        name="Methanol stripping column, condenser, product tankage, "
             "truck loading",
        basis_cost=_GLAMOUR_ISBL_USD_2010 * 0.20 + 0.50e6,
        basis_capacity=24455.0,
        capacity=crude_tpy,
        exponent=0.60,
        cepci_year=2010,
        capacity_unit="t/yr crude glycerol fed",
        source="[CAPEX-1] ISBL apportioned to the methanol recovery block "
               "(engineering estimate, 20% of pretreatment ISBL) plus a "
               "USD 0.50M allowance for storage and loading",
    )


# ----------------------------------------------------------------------------
# Purification block, shared by C1, C2 and the aggregation variant E3
# ----------------------------------------------------------------------------

C1_RECOVERY = (1 - PRETREATMENT_GLYCEROL_LOSS) * LURGI_RECOVERY_TO_PRIME  # 0.9016
C1_PRODUCT_TPY = GLYCEROL_TPY * C1_RECOVERY / 0.995
SECOND_CUT_TPY = GLYCEROL_TPY * LURGI_TO_SECOND_CUT / 0.87
RESIDUE_TPY = WET_SALT_CAKE_TPY + GLYCEROL_TPY * 0.05 + 150   # + heavies/MONG


def purification_streams(product_tpy, second_cut_tpy, scale=1.0):
    """Section F credits, purchased inputs and utilities for a purification
    train, linear in throughput except where a published per-tonne-of-product
    factor applies."""
    return dict(
        credits=[
            Stream("Methanol recovered and returned to the biodiesel plant",
                   METHANOL_RECOVERED_TPY * scale, "methanol",
                   f"900 t/yr in feed x {METHANOL_RECOVERY:.0%} recovery x "
                   f"{scale:.1f} throughput"),
            Stream("Recovered FAME from the acidulation top phase",
                   FAME_TPY * 0.90 * scale, "recovered_fame",
                   f"{FAME_TPY:.0f} t/yr in feed x 90% recovery"),
            Stream("Split soap fatty acids (acid oil)",
                   FFA_FROM_SOAP * 0.90 * scale, "acid_oil_ffa",
                   f"{SOAP_TPY:.0f} t soap -> {FFA_FROM_SOAP:.0f} t FFA x 90%"),
            Stream("Second-cut glycerine (85-90%) sold as crude",
                   second_cut_tpy, "crude_glycerol",
                   "3% of glycerol per the Lurgi yield block"),
        ],
        purchased=[
            Stream("Sulphuric acid (93%)", H2SO4_TPY * scale, "sulfuric_acid",
                   f"{ACID_FOR_SOAP:.1f} t soap splitting + "
                   f"{ACID_FOR_ALKALI:.1f} t alkali neutralisation, "
                   f"x{ACID_EXCESS} excess"),
            Stream("Activated carbon", CARBON_T_PER_T * product_tpy,
                   "activated_carbon", "9 lb/t product (Lurgi basis)"),
            Stream("Caustic soda for pH trim", NAOH_T_PER_T * product_tpy,
                   "caustic_soda", "7.5 lb/t of 45% solution (Lurgi basis)"),
            Stream("Salt cake and still residue disposal", RESIDUE_TPY * scale,
                   "solid_waste_disposal",
                   f"{WET_SALT_CAKE_TPY:.0f} t wet salt cake + "
                   f"{GLYCEROL_TPY * 0.05:.0f} t glycerol to residue + "
                   f"150 t heavies/MONG, x{scale:.1f}"),
        ],
        # All gas here raises steam, so the DOE total-steam-generation factor
        # applies on top of the fired-fuel duty (see params.STEAM_SYSTEM_SOURCE).
        gas_mmbtu_yr=(STEAM_T_PER_T_PRODUCT * product_tpy * STEAM_GJ_PER_T
                      / GJ_PER_MMBTU / BOILER_EFFICIENCY
                      + (MEOH_COLUMN_MMBTU + EVAP_MMBTU) * scale
                      ) * STEAM_SYSTEM_FACTOR,
        elec_kwh_yr=ELEC_KWH_PER_T * product_tpy,
        cooling_water_m3_yr=CW_M3_PER_T * product_tpy,
        wastewater_m3_yr=WW_M3_PER_T * product_tpy + 12000 * scale,
    )


def aggregation_route(crude_tpy, code="E3"):
    """Technical-grade purification sized for the client's own crude PLUS
    third-party crude bought in at the same assessed price.

    This is the variant the brief invites in Section 2: it attacks the scale
    problem instead of accepting it. Tripling throughput multiplies ISBL by
    3^0.6 = 1.93 and staffing by 3^0.35 = 1.47; total fixed opex rises 1.79x
    because maintenance and insurance follow FCI rather than headcount. Against
    3x the crude, fixed cost per tonne of crude fed falls 40%, from $314/t to
    $187/t, and that reduction is the whole of the improvement.

    It is not enough. With inbound freight charged on bought-in crude - which
    is unavoidable, since crude glycerine is assessed FOB - the capacity at
    which this flowsheet reaches NPV = 0 is about 54,600 t/yr, which is ~130%
    of the entire estimated PADD 1 crude glycerol pool. Aggregation therefore
    fails on FEEDSTOCK AVAILABILITY, not on economics: the economics work, but
    only at a scale the region cannot supply.
    """
    scale = crude_tpy / CRUDE_TPY
    third_party = max(0.0, crude_tpy - CRUDE_TPY)
    glycerol = crude_tpy * 0.80
    product = glycerol * C1_RECOVERY / 0.995
    second_cut = glycerol * LURGI_TO_SECOND_CUT / 0.87

    streams = purification_streams(product, second_cut, scale=scale)
    streams["purchased"] = [
        Stream("Third-party crude glycerol purchased", third_party,
               "crude_glycerol",
               f"{third_party:,.0f} t/yr bought in at the SAME Argus assessment "
               f"used for the internal transfer price - no discount assumed"),
        # Omitted in the first pass and it should not have been. Crude glycerol
        # is assessed FOB, so the buyer carries the freight, and the further
        # the gathering radius extends the more of it there is. This is the
        # cost that makes aggregation self-limiting.
        Stream("Inbound freight on third-party crude", third_party,
               "freight_out",
               "Crude glycerine is assessed FOB, so inbound haulage is the "
               "buyer's cost. Charged at the same road-freight rate as "
               "outbound product."),
    ] + streams["purchased"]

    return Route(
        code=code,
        name=f"Regional aggregation refinery ({crude_tpy:,.0f} t/yr crude)",
        category="E. Low-capex / formulated",
        description=(
            f"Build the C1 train at {crude_tpy:,.0f} t/yr: the client's own "
            f"10,000 t/yr plus {third_party:,.0f} t/yr of third-party crude "
            f"from other Northeast producers. Capex rises 1.93x for 3x "
            f"throughput while fixed opex rises only 1.79x, cutting fixed cost "
            f"from $314 to $187 per tonne of crude fed. Feedstock basis: EIA counts 9 "
            f"biodiesel plants in PADD 1 with 128 MMgy aggregate capacity; at "
            f"~10 wt% glycerol yield that is roughly 42,000 t/yr of regional "
            f"crude, of which this client is already 10,000 t/yr. Named "
            f"regional producers include United Biodiesel (NY, 50 MMgy), "
            f"Hero BX Erie (PA, 50 MMgy) and World Energy Harrisburg (PA, "
            f"50 MMgy)."
        ),
        crude_fed_tpy=crude_tpy,
        glycerol_fed_tpy=glycerol,
        glycerol_conversion=C1_RECOVERY,
        product_name="Technical grade glycerine 99.5%",
        product_price_key="technical_glycerine",
        product_purity=0.995,
        capex_items=[pretreatment_capex(crude_tpy), distillation_capex(crude_tpy),
                     polishing_capex(crude_tpy)],
        # Fixed staffing scales far more weakly than throughput: the same
        # control room and the same distillation train run a larger column.
        operators_per_shift=1.5 * (scale ** 0.35),
        extra_fixed_opex=250000.0 if third_party > 0 else 0.0,
        extra_fixed_opex_note=(
            "Feedstock origination, inbound logistics scheduling and incoming "
            "quality control on third-party crude of variable specification."
        ),
        **streams,
    )


# ============================================================================
# ROUTES
# ============================================================================

def build_routes():
    routes = []

    # ---- A. Baseline / no-build -------------------------------------------
    routes.append(Route(
        code="A1",
        name="Sell crude glycerol as-is to a merchant refiner",
        category="A. Baseline",
        description=(
            "The null hypothesis. Load 10,000 t/yr of 80% crude into trucks or "
            "rail at the gate and sell on the Argus fob US Midwest crude "
            "assessment. Zero capex, zero incremental operating cost. Because "
            "every other route is charged the same price as an internal "
            "transfer, this route scores EXACTLY zero margin per tonne by "
            "construction, and that zero is the hurdle."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=0.0,
        product_name="(none - feed sold directly)",
        product_price_key="",
        freight_applies=False,
        charge_feed=True,
        credits=[Stream("Crude glycerol sold fob plant", CRUDE_TPY,
                        "crude_glycerol", "10,000 t/yr as-is, no processing")],
        operators_per_shift=0.0,
    ))

    routes.append(Route(
        code="A2",
        name="Pay for disposal / anaerobic digestion offtake",
        category="A. Baseline",
        description=(
            "Downside case. If crude glycerol markets go negative - which they "
            "did in 2007-08 and again briefly in the 2023-24 oversupply - the "
            "producer pays to move the stream. Carried to bound the downside, "
            "not as a recommendation."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=0.0,
        product_name="(none - disposal)",
        product_price_key="",
        freight_applies=False,
        charge_feed=True,
        purchased=[Stream("Disposal / AD offtake gate fee", CRUDE_TPY,
                          "solid_waste_disposal", "10,000 t/yr at the "
                          "non-hazardous liquid waste gate fee")],
        operators_per_shift=0.0,
        gate_scale_fit="fail",
        gate_note="Value-destroying by inspection whenever the crude market is "
                  "positive. Retained only as the downside bound.",
    ))

    # ---- B. Energy / internal use -----------------------------------------
    # Crude glycerol HHV, mass-weighted:
    #   glycerol 18.0, methanol 22.7, FAME 40.0, soaps 38.0 MJ/kg; water/salt 0
    hhv = (0.80 * 18.0 + 0.09 * 22.7 + 0.03 * 40.0 + 0.015 * 38.0)   # 18.2 MJ/kg
    fuel_gj = CRUDE_TPY * hhv                                        # 182,205 GJ/yr
    glycerol_boiler_eff = 0.75      # wet, ashy, corrosive fuel; poor turndown
    useful_gj = fuel_gj * glycerol_boiler_eff
    gas_displaced_mmbtu = useful_gj / BOILER_EFFICIENCY / GJ_PER_MMBTU

    routes.append(Route(
        code="B1",
        name="Combust for process steam at the biodiesel plant",
        category="B. Energy / internal",
        description=(
            f"Burn all 10,000 t/yr in a dedicated boiler to displace purchased "
            f"natural gas. Crude HHV computed at {hhv:.1f} MJ/kg mass-weighted, "
            f"{glycerol_boiler_eff:.0%} boiler efficiency on this fuel (wet, "
            f"ashy, corrosive, poor turndown), displacing gas raised at "
            f"{BOILER_EFFICIENCY:.0%}. Acrolein forms below ~350 C so the "
            f"burner must hold high flame temperature; ash slags the tubes."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=0.0,
        product_name="Displaced natural gas",
        product_price_key="",
        freight_applies=False,
        credits=[Stream("Natural gas displaced", gas_displaced_mmbtu,
                        "natural_gas",
                        f"{fuel_gj:,.0f} GJ/yr fuel x {glycerol_boiler_eff:.0%} "
                        f"boiler / {BOILER_EFFICIENCY:.0%} gas boiler")],
        purchased=[Stream("Ash and slag disposal", 200.0, "solid_waste_disposal",
                          "Inorganic ash plus soot")],
        capex_items=[CapexItem(
            name="Glycerol-fired boiler, burner, ash handling, flue gas treatment",
            basis_cost=4.0e6, basis_capacity=10000.0, capacity=CRUDE_TPY,
            exponent=0.60, cepci_year=2024,
            capacity_unit="t/yr crude glycerol fired",
            source="ENGINEERING ESTIMATE - no published basis located for a "
                   "glycerol-fired package boiler of this duty. Flagged as a "
                   "placeholder; the conclusion is insensitive to it because "
                   "the route loses money on fuel value alone.",
        )],
        operators_per_shift=0.3,
        gate_note="Passes all technical gates; killed on economics, not feasibility.",
    ))

    # ---- C. Midstream purification ----------------------------------------
    c1_recovery = C1_RECOVERY
    c1_product = C1_PRODUCT_TPY
    second_cut = SECOND_CUT_TPY
    residue_tpy = RESIDUE_TPY

    routes.append(Route(
        code="C1",
        name="Purify to technical grade (99.5%)",
        category="C. Midstream purification",
        description=(
            "Acidulation, phase split, methanol recovery, evaporation, then "
            "vacuum distillation with live-steam stripping and activated-carbon "
            "bleaching. Sold on the Argus technical grade 99.5% assessment. "
            f"Glycerol recovery {c1_recovery:.1%} overall "
            f"({1 - PRETREATMENT_GLYCEROL_LOSS:.0%} through pretreatment x "
            f"{LURGI_RECOVERY_TO_PRIME:.0%} Lurgi distillation yield)."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=c1_recovery,
        selectivity=1.0,
        mass_yield_ratio=1.0,
        product_name="Technical grade glycerine 99.5%",
        product_price_key="technical_glycerine",
        product_purity=0.995,
        capex_items=[pretreatment_capex(), distillation_capex(CRUDE_TPY),
                     polishing_capex(CRUDE_TPY)],
        operators_per_shift=1.5,
        extra_fixed_opex_note=(
            "1.5 operators/shift assumes the unit is a BOLT-ON at the existing "
            "biodiesel plant and shares site services, laboratory, maintenance "
            "shop and administration. A greenfield would need roughly double."
        ),
        **purification_streams(c1_product, second_cut),
    ))

    c2_recovery = c1_recovery * 0.99      # ion-exchange / polishing loss
    c2_product = GLYCEROL_TPY * c2_recovery / 0.997
    c2_streams = purification_streams(c2_product, second_cut)

    routes.append(Route(
        code="C2",
        name="Purify to USP/EP grade (99.7%)",
        category="C. Midstream purification",
        description=(
            "C1 plus ion exchange, polish bleaching, deodorisation and the "
            "cGMP-adjacent quality system. Revenue in operating years 1-2 is "
            "held at the technical-grade price to represent the customer "
            "qualification lag, which is a commercial cost the purity number "
            "on the spec sheet does not capture."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=c2_recovery,
        product_name="USP/EP glycerine 99.7%",
        product_price_key="usp_glycerine",
        product_purity=0.997,
        capex_items=[pretreatment_capex(), distillation_capex(CRUDE_TPY),
                     polishing_capex(CRUDE_TPY),
                     ion_exchange_capex(CRUDE_TPY)],
        operators_per_shift=1.8,
        extra_fixed_opex=350000.0,
        extra_fixed_opex_note=(
            "USD 350k/yr for the cGMP-adjacent quality system: QA manager, "
            "batch documentation, stability and release testing, customer and "
            "third-party audits."
        ),
        revenue_ramp=[1250.0 / 1530.0, 1250.0 / 1530.0] + [1.0] * 13,
        ramp_note=(
            "Operating years 1-2 priced at technical grade (ratio of the two "
            "base prices) because USP customers qualify a new source over "
            "12-24 months. Brief Trap 4."
        ),
        **c2_streams,
    ))

    routes.append(Route(
        code="C3",
        name="Membrane / ion-exchange-led purification (no distillation)",
        category="C. Midstream purification",
        description=(
            "Lower energy, higher consumables. Attractive in principle at this "
            "scale given New York gas prices. Killed on published performance: "
            "the only TEA located at this exact scale reports the membrane "
            "route reaching 93.9% purity at 86.2% recovery and the ion-exchange "
            "route consuming 81.7 units of raw material per unit product, with "
            "both routes LOSS-MAKING where vacuum distillation is marginally "
            "profitable."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=0.862,
        product_name="Purified glycerine 93.9%",
        product_price_key="feed_grade_glycerin",
        product_purity=0.939,
        operators_per_shift=1.5,
        gate_technical_readiness="fail",
        gate_note=(
            "Cannot reach the 99.5% technical specification, so it does not "
            "access the refined price tier that justifies the investment. "
            "Bansod et al. 2025 report annual profit of -USD 2.72M (membrane) "
            "and -USD 11.42M (ion exchange) at 1,000 kg/h."
        ),
    ))

    # ---- D. Downstream conversion -----------------------------------------
    # D1 Propylene glycol. C3H8O3 + H2 -> C3H8O2 + H2O
    # MW glycerol 92.09, PG 76.10, H2 2.016
    pg_mass_yield = 76.10 / 92.09                     # 0.8264 t PG / t glycerol
    h2_stoich = 2.016 / 92.09                         # 0.02189 t H2 / t glycerol
    # Sourced kinetics, not optimistic ones. J. Ind. Eng. Chem. 2017
    # (10.1016/j.jiec.2017.05.040), commercial Cu catalyst, 483-513 K,
    # 6.5-8.0 MPa, H2:glycerol = 5: 90-95% PG selectivity at 20-75% conversion.
    # Dasari et al., Appl. Catal. A 281 (2005) 225-231, copper chromite at
    # 200 C / 13.8 bar, is markedly worse - 54.8% conversion at 85% selectivity
    # on a 20 wt% water feed - and selectivity FALLS above 200 C because the
    # PG itself is over-hydrogenolysed. 75%/90% is the top of the sourced band.
    pg_conversion, pg_selectivity = 0.75, 0.90
    glycerol_to_reactor = GLYCEROL_TPY * c1_recovery  # must be REFINED first
    # Net purchase is essentially stoichiometric once excess H2 is recycled:
    # Renewable Energy 2020 (10.1016/j.renene.2020.05.072) reports 22 kg/h H2
    # for 821 kg/h PG = 26.8 kg/t PG against 26.5 stoichiometric. The 5:1 molar
    # inlet ratio everyone uses sizes the recycle compressor, not the purchase,
    # and E3S Conf. 2020 warns that above 5:1 methane selectivity approaches
    # 100% - you burn the hydrogen you bought.
    h2_tpy = glycerol_to_reactor * h2_stoich * 1.05

    routes.append(Route(
        code="D1",
        name="Propylene glycol via hydrogenolysis",
        category="D. Downstream conversion",
        description=(
            "Cu- or Ru-catalysed hydrogenolysis at roughly 200-260 C and 25-80 "
            "bar H2. CRITICALLY, the catalyst is poisoned by sodium, chloride "
            "and soaps, so this route does not replace the purification plant - "
            "it sits ON TOP of it, and carries the full C1 capex plus a "
            "high-pressure hydrogenation train. The comparison that matters is "
            "therefore incremental against C1, not against A1."
        ),
        glycerol_fed_tpy=glycerol_to_reactor,
        glycerol_conversion=pg_conversion,
        selectivity=pg_selectivity,
        mass_yield_ratio=pg_mass_yield,
        product_name="Propylene glycol (industrial/USP)",
        product_price_key="propylene_glycol",
        product_purity=0.995,
        credits=[
            Stream("Methanol recovered", METHANOL_RECOVERED_TPY, "methanol",
                   "Front-end credit, unchanged from C1"),
            Stream("Recovered FAME", FAME_TPY * 0.90, "recovered_fame",
                   "Front-end credit, unchanged from C1"),
            Stream("Split soap fatty acids", FFA_FROM_SOAP * 0.90,
                   "acid_oil_ffa", "Front-end credit, unchanged from C1"),
        ],
        purchased=[
            Stream("Merchant hydrogen, delivered", h2_tpy, "hydrogen",
                   f"{glycerol_to_reactor:,.0f} t glycerol x {h2_stoich:.5f} "
                   f"t H2/t x 1.25 for purge and excess"),
            Stream("Sulphuric acid (93%)", H2SO4_TPY, "sulfuric_acid",
                   "Front-end, unchanged from C1"),
            Stream("Salt cake and residue disposal", residue_tpy,
                   "solid_waste_disposal", "Front-end, unchanged from C1"),
        ],
        gas_mmbtu_yr=c2_streams["gas_mmbtu_yr"] * 1.25,
        elec_kwh_yr=glycerol_to_reactor * 220.0,    # recycle compressor duty
        cooling_water_m3_yr=c2_streams["cooling_water_m3_yr"] * 1.3,
        wastewater_m3_yr=glycerol_to_reactor * 0.25,
        capex_items=[
            pretreatment_capex(),
            distillation_capex(CRUDE_TPY),
            polishing_capex(CRUDE_TPY),
            CapexItem(
                name="Hydrogenolysis: high-pressure reactor, H2 recycle "
                     "compressor, PG/water separation train, catalyst handling",
                basis_cost=15.3e6, basis_capacity=45000.0,
                capacity=(glycerol_to_reactor * pg_conversion * pg_selectivity
                          * pg_mass_yield),
                exponent=0.65, cepci_year=2013,
                capacity_unit="t/yr propylene glycol produced",
                source="University of Pennsylvania senior design, bare-module "
                       "cost USD 15.3M for ~100 MM lb/yr (45,000 t/yr) PG, "
                       "2013 construction year (via Focus on Catalysts 2013, "
                       "10.1016/s1351-4180(13)70125-9). Cross-check: Energies "
                       "2021, 14, 5081 reports TCI USD 15.46M at ~20,000 t/yr "
                       "PG. Exponent 0.65 because high-pressure hydrogen "
                       "service scales down poorly.",
            ),
        ],
        operators_per_shift=3.5,
        extra_fixed_opex=400000.0,
        extra_fixed_opex_note="Catalyst replacement and hydrogen supply contract "
                              "standby charges.",
        gate_raw_material="fail",
        gate_note=(
            "Fails the raw-material gate. A 10,000 t/yr site is a tube-trailer "
            "hydrogen customer, not a pipeline customer, and pays a large "
            "premium over the refinery-scale hydrogen prices assumed in the "
            "academic literature on this reaction. Retained through Pass 2 "
            "anyway so the loss is quantified rather than asserted."
        ),
    ))

    # D2-D12: killed at Pass 1. Documented in gate_table() below.
    for code, name, kwargs in _conversion_routes_killed_at_gate():
        routes.append(Route(code=code, name=name,
                            category="D. Downstream conversion",
                            glycerol_fed_tpy=GLYCEROL_TPY, **kwargs))

    # ---- E. Low-capex / formulated ----------------------------------------
    e1_product = CRUDE_TPY - METHANOL_RECOVERED_TPY      # 9,145 t/yr

    routes.append(Route(
        code="E1",
        name="De-methanolised feed-grade glycerin",
        category="E. Low-capex / formulated",
        description=(
            "The minimum intervention that changes the product's commercial "
            "identity. A single stripping column takes methanol from 9 wt% to "
            "below the AAFCO 5,000 ppm limit - and below the tighter 1,000 ppm "
            "Canadian beef-cattle limit - turning a discounted crude into a "
            "consistent, specification-controlled feed ingredient, while "
            "recovering 855 t/yr of methanol to the biodiesel plant. No "
            "acidulation, no distillation, no salt cake."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=1.0,
        product_name="Feed-grade glycerin (~87.5% glycerol, low methanol)",
        product_price_key="feed_grade_glycerin",
        product_purity=GLYCEROL_TPY / e1_product,   # as-sold basis
        # No freight deduction: the kosher-crude assessment this price is
        # derived from is itself fob plant, matching the A1 baseline.
        freight_applies=False,
        credits=[Stream("Methanol recovered and returned to the biodiesel plant",
                        METHANOL_RECOVERED_TPY, "methanol",
                        f"900 t/yr x {METHANOL_RECOVERY:.0%}")],
        gas_mmbtu_yr=MEOH_COLUMN_MMBTU * STEAM_SYSTEM_FACTOR,
        elec_kwh_yr=120000.0,
        cooling_water_m3_yr=180000.0,
        wastewater_m3_yr=3000.0,
        capex_items=[methanol_only_capex()],
        operators_per_shift=0.4,
        extra_fixed_opex=80000.0,
        extra_fixed_opex_note=(
            "AAFCO ingredient registration, batch certificates of analysis, "
            "and periodic methanol/glycerol/ash assay."
        ),
    ))

    routes.append(Route(
        code="E2",
        name="De-icer / dust suppressant blend component",
        category="E. Low-capex / formulated",
        description=(
            "Blend de-methanolised crude into a liquid de-icer or dust "
            "suppressant. Upstate New York is a genuine de-icer market."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=1.0,
        product_name="De-icer blend component",
        product_price_key="feed_grade_glycerin",
        product_purity=GLYCEROL_TPY / e1_product,
        operators_per_shift=0.4,
        gate_scale_fit="fail",
        gate_note=(
            "Municipal de-icer demand is seasonal and intensely price-"
            "competitive against salt brine and calcium chloride; 9,000 t/yr "
            "of year-round production cannot be placed into a four-month "
            "regional window without storage the project cannot justify. "
            "Dominated by E1, which uses the same equipment for a year-round "
            "market."
        ),
    ))

    # E3: the scale fix. Build for regional third-party crude as well.
    routes.append(aggregation_route(30000.0, code="E3"))

    # ---- F. Side-stream monetisation --------------------------------------
    routes.append(Route(
        code="F1",
        name="Methanol recovery only (return to biodiesel plant)",
        category="F. Side-stream only",
        description=(
            "Strip methanol and return it; sell the remaining crude on the "
            "ordinary crude assessment with no quality premium claimed. This "
            "isolates the value of the methanol credit ALONE, so that the "
            "premium E1 attributes to the feed specification can be read "
            "directly as the difference between the two routes."
        ),
        glycerol_fed_tpy=GLYCEROL_TPY,
        glycerol_conversion=0.0,
        product_name="(crude sold, methanol returned)",
        product_price_key="",
        freight_applies=False,
        credits=[
            Stream("De-methanolised crude sold at the ordinary crude price",
                   e1_product, "crude_glycerol",
                   "10,000 t/yr less 855 t/yr methanol removed"),
            Stream("Methanol recovered", METHANOL_RECOVERED_TPY, "methanol",
                   f"900 t/yr x {METHANOL_RECOVERY:.0%}"),
        ],
        gas_mmbtu_yr=MEOH_COLUMN_MMBTU * STEAM_SYSTEM_FACTOR,
        elec_kwh_yr=120000.0,
        cooling_water_m3_yr=180000.0,
        wastewater_m3_yr=3000.0,
        capex_items=[methanol_only_capex()],
        operators_per_shift=0.4,
    ))

    return routes


def _conversion_routes_killed_at_gate():
    """Conversion routes eliminated in Pass 1, each with a one-line reason."""
    common = dict(glycerol_conversion=0.0, product_name="(killed at Pass 1)",
                  product_price_key="", freight_applies=False)
    return [
        ("D2", "1,3-propanediol (fermentation or catalytic)", dict(
            **common, gate_chemcad="fail", gate_technical_readiness="fail",
            gate_note="Biological reactor with live-organism kinetics that "
                      "CHEMCAD handles poorly, and the catalytic route is not "
                      "commercially demonstrated outside DuPont/Tate & Lyle's "
                      "captive corn-sugar process. Brief Section 2 makes "
                      "CHEMCAD tractability a real selection criterion.")),
        ("D3", "Epichlorohydrin via hydrochlorination (Epicerol-type)", dict(
            **common, gate_scale_fit="fail", gate_raw_material="fail",
            gate_note="SOURCED KILL ON SCALE. The smallest glycerol-to-ECH plant "
                      "ever BUILT is Meghmani Finechem, Dahej, at 50,000 t/yr "
                      "(INR 275 crore, commissioned 2022); the smallest unit any "
                      "licensor offers is 30,000 t/yr. This site would make "
                      "~7,300 t/yr - 15% of the smallest plant ever built. Both "
                      "Solvay Epicerol plants (Tavaux 10 kt/yr pilot, Map Ta Phut "
                      "100 kt/yr) were bolted onto EXISTING chlor-alkali "
                      "complexes, because the route needs captive HCl: "
                      "stoichiometry is 0.974 t HCl per t ECH, or ~7,100 t/yr "
                      "here, and anhydrous HCl logistics to a rural New York site "
                      "are a showstopper on their own. The product is also "
                      "structurally oversupplied - SunSirs reports ~140 kt of new "
                      "Chinese capacity in 2024 and ~170 kt in 2025 against much "
                      "slower demand growth, with a 46.9% intra-year price swing "
                      "in 2025. NA price $1,350-1,750/t.")),
        ("D4", "Acrolein / acrylic acid via dehydration-oxidation", dict(
            **common, gate_safety_permitting="fail", gate_scale_fit="fail",
            gate_note="Acrolein is an extreme acute inhalation hazard "
                      "(IDLH 2 ppm) requiring containment and emergency "
                      "response capability a mid-size producer does not have. "
                      "Acrylic acid is a 6 Mt/yr world-scale commodity.")),
        ("D5", "Glycerol carbonate (DMC or urea transesterification)", dict(
            **common, gate_scale_fit="fail",
            gate_note="SOURCED KILL ON MARGIN, not just absorption. Two 2025/26 "
                      "TEAs converge on a selling price of ~$3,500/t, and a 2023 "
                      "study puts the profitability threshold at $3,150/t - so "
                      "the headroom is thin to begin with. Buying DMC rather than "
                      "making it cuts capex to ~$7.4M but raises total annualised "
                      "cost to ~$3,102/t against a $3,000-3,500/t price: "
                      "essentially zero margin before any scale penalty. "
                      "Integrated DMC production removes the reagent cost but "
                      "needs $25-30M of capex, which is the whole problem again. "
                      "Market absorption is a secondary concern: ~10,260 t/yr "
                      "from this site would be 7-16% of a 65,000-150,000 t/yr "
                      "world market in which the top three producers hold "
                      "91-94% share.")),
        ("D6", "Solketal (ketalisation with acetone)", dict(
            **common, gate_scale_fit="fail", gate_raw_material="fail",
            gate_note="SOURCED KILL ON MARKET SIZE. The capex is genuinely small "
                      "($1-3M TCI for a 4,000-20,000 t/yr glycerol feed, the best "
                      "capex fit in the entire conversion set) and the chemistry "
                      "is mild. It dies on the market: the world MERCHANT solketal "
                      "market is roughly 5,600 t/yr and SHRINKING at about -5%/yr, "
                      "while this site would produce ~11,500 t/yr - about twice "
                      "the entire world market. Economics also require solketal "
                      "above ~$2,400/t at a 4,000 t/yr glycerol feed, and the "
                      "fuel-oxygenate application that could absorb the volume "
                      "cannot pay it. Acetone consumption 0.495 t/t solketal.")),
        ("D7", "Glycerol tert-butyl ethers (GTBE)", dict(
            **common, gate_raw_material="fail",
            gate_note="Requires reliable isobutylene, which a rural New York "
                      "site cannot source at this scale without a dedicated "
                      "supply chain.")),
        ("D8", "Dihydroxyacetone (DHA) via oxidation or fermentation", dict(
            **common, gate_scale_fit="fail", gate_chemcad="fail",
            gate_note="THE MOST EMPHATIC SCALE FAILURE IN THE SET, now sourced. "
                      "The global DHA market is 2,000-6,000 t/yr. Converting this "
                      "site's glycerol would yield ~7,800 t/yr - MORE THAN 100% OF "
                      "WORLD DEMAND from a single mid-size biodiesel producer. "
                      "Price data is unusable anyway: the widely cited $150/kg "
                      "traces to a 2015 figure in Ciriminna et al. (ChemistryOpen "
                      "2018), which itself warns that public DHA prices 'differ "
                      "greatly', against current Chinese bulk offers of $20-50/kg. "
                      "The fermentation route is also poorly CHEMCAD-tractable.")),
        ("D9", "Lactic / succinic / citric acid via fermentation", dict(
            **common, gate_chemcad="fail", gate_feed_tolerance="fail",
            gate_note="Live-organism kinetics outside CHEMCAD's competence, and "
                      "the salts and soaps in this feed inhibit the organisms, "
                      "so purification capex is required first anyway. "
                      "Fermentation also competes against dextrose feedstock "
                      "that is cheaper per unit carbon.")),
        ("D10", "Polyglycerols and polyglycerol esters", dict(
            **common, gate_scale_fit="fail",
            gate_note="The best scale fit of the conversion set and the closest "
                      "call in Pass 1. Killed on commercial rather than "
                      "technical grounds: polyglycerol esters are sold on "
                      "application performance into food and personal care, "
                      "requiring a formulation and regulatory capability, and "
                      "multi-year customer qualification, that the client does "
                      "not have. Flagged as the conversion route to revisit "
                      "first if the client acquires a specialty channel.")),
        ("D11", "Acetol / hydroxyacetone; allyl alcohol", dict(
            **common, gate_scale_fit="fail", gate_technical_readiness="fail",
            gate_note="No merchant market of consequence for acetol; it is "
                      "essentially an intermediate to propylene glycol, which "
                      "is already evaluated as D1.")),
        ("D12", "Triacetin via acetylation", dict(
            **common, gate_raw_material="fail",
            gate_note="CORRECTED ARITHMETIC. Stoichiometry is 3.326 t acetic "
                      "anhydride per t glycerol, yielding 2.369 t triacetin and "
                      "1.956 t acetic acid. At sourced prices that is $2,993/t of "
                      "reagent against $3,080/t of triacetin revenue - the "
                      "anhydride does not quite exceed the revenue, as an earlier "
                      "draft of this screen asserted, but it consumes 97% of it. "
                      "That leaves $87 per tonne of glycerol to pay for the "
                      "glycerol itself (~$500/t on a glycerol basis), capex, "
                      "utilities and labour, so the route is decisively negative "
                      "unless the 1.956 t/t of by-product acetic acid can be "
                      "monetised - roughly 15,600 t/yr of a commodity this client "
                      "has no channel for. Acetic anhydride is also a DEA List I "
                      "controlled precursor carrying registration and "
                      "recordkeeping obligations. The acetic-acid route avoids "
                      "the controlled precursor but is equilibrium-limited and "
                      "needs continuous water removal.")),
    ]
