"""
Runs the three-pass screen, the Pass-3 finalist analysis, sensitivity,
breakevens and Monte Carlo, then exports everything to a traceable workbook.

    python -m tea.run
"""

import os
import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .model import economics
from .params import (
    PRICES, FIN, CRUDE_TPY, GLYCEROL_TPY, FEED_TPY, CEPCI_CURRENT,
    CEPCI_SOURCE, GLYCERINE_HISTORY, CENTS_LB_TO_USD_T, MACRS_NOTE,
    CAPEX_ACCURACY, DISCOUNT_RATE_JUSTIFICATION, STRANDING_BARRIER,
)
from .routes import build_routes, aggregation_route

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "outputs")
FINALISTS = ["A1", "E1", "C1", "C2", "E3"]


# ----------------------------------------------------------------------------
# Pass 1 and Pass 2
# ----------------------------------------------------------------------------

def pass1_table(routes):
    rows = []
    for r in routes:
        rows.append({
            "Code": r.code, "Route": r.name, "Category": r.category,
            "Technical readiness": r.gate_technical_readiness,
            "Scale fit": r.gate_scale_fit,
            "Raw material": r.gate_raw_material,
            "Safety / permitting": r.gate_safety_permitting,
            "CHEMCAD tractability": r.gate_chemcad,
            "Feed tolerance": r.gate_feed_tolerance,
            "Result": "PASS" if r.gates_passed else "FAIL",
            "Failed gate(s)": ", ".join(r.failed_gates),
            "Reason": r.gate_note,
        })
    return pd.DataFrame(rows)


def pass2_table(results):
    rows = []
    for e in results:
        carried = e["gates_passed"] or e["product_tpy"] > 0 or e["code"] == "A2"
        rows.append({
            "Code": e["code"], "Route": e["name"],
            "Gate": "PASS" if e["gates_passed"] else "FAIL",
            "Crude fed (t/yr)": e["crude_fed_tpy"],
            "Product": e["product"],
            "Product (t/yr)": e["product_tpy"] if carried else np.nan,
            "Net price ($/t)": e["net_product_price_$_t"] if carried else np.nan,
            "Product revenue ($M)": e["product_revenue_$"] / 1e6 if carried else np.nan,
            "Section F credits ($M)": e["credit_revenue_$"] / 1e6 if carried else np.nan,
            "Feed cost ($M)": e["feed_cost_$"] / 1e6 if carried else np.nan,
            "Variable opex ($M)": e["variable_opex_$"] / 1e6 if carried else np.nan,
            "Fixed opex ($M)": e["fixed_opex_$"] / 1e6 if carried else np.nan,
            "EBITDA ($M)": e["EBITDA_$"] / 1e6 if carried else np.nan,
            "MARGIN $/t crude fed": e["margin_per_t_crude_$"] if carried else np.nan,
            "TCI ($M)": e["TCI_$"] / 1e6 if carried else np.nan,
            "Simple ROI": e["simple_ROI"] if carried and e["TCI_$"] > 0 else np.nan,
            "Payback (yr)": e["payback_years"] if carried and e["TCI_$"] > 0 else np.nan,
            "NPV @12% ($M)": e["NPV_$"] / 1e6 if carried else np.nan,
            "IRR": e["IRR"] if carried else np.nan,
        })
    df = pd.DataFrame(rows)
    return df.sort_values("MARGIN $/t crude fed", ascending=False,
                          na_position="last").reset_index(drop=True)


# ----------------------------------------------------------------------------
# Sensitivity
# ----------------------------------------------------------------------------

TORNADO_VARS = [
    ("technical_glycerine", "Technical glycerine price"),
    ("crude_disposal_cost", "Crude glycerol disposal cost (client invoice)"),
    ("merchant_crude_glycerol", "Merchant crude (third-party purchase)"),
    ("feed_grade_glycerin", "Feed-grade / de-methanolised product price"),
    ("natural_gas", "Natural gas (New York industrial)"),
    ("methanol", "Methanol credit"),
    ("operator_burdened", "Burdened labour rate"),
    ("recovered_fame", "Recovered FAME credit"),
    ("acid_oil_ffa", "Split soap fatty acid (acid oil) credit"),
    ("solid_waste_disposal", "Salt cake and residue disposal"),
    ("sulfuric_acid", "Sulphuric acid"),
    ("electricity", "Electricity"),
    ("freight_out", "Freight, outbound product and inbound third-party crude"),
    ("caustic_soda", "Caustic soda"),
    ("activated_carbon", "Activated carbon"),
]


def tornado(route, extra_capex=True):
    base = economics(route)["NPV_$"]
    rows = []
    for key, label in TORNADO_VARS:
        p = PRICES[key]
        lo = economics(route, price_overrides={key: p.low})["NPV_$"]
        hi = economics(route, price_overrides={key: p.high})["NPV_$"]
        rows.append({
            "Variable": label, "Price key": key,
            "Low value": p.low, "Base value": p.base, "High value": p.high,
            "Unit": p.unit, "Confidence": p.confidence,
            "NPV at low ($M)": lo / 1e6, "NPV base ($M)": base / 1e6,
            "NPV at high ($M)": hi / 1e6,
            "Swing ($M)": abs(hi - lo) / 1e6,
        })
    if extra_capex:
        lo = economics(route, capex_multiplier=0.70)["NPV_$"]
        hi = economics(route, capex_multiplier=1.50)["NPV_$"]
        rows.append({
            "Variable": "Capex accuracy (AACE Class 4, -30%/+50%)",
            "Price key": "capex_multiplier",
            "Low value": 0.70, "Base value": 1.00, "High value": 1.50,
            "Unit": "multiplier on ISBL", "Confidence": "estimate",
            "NPV at low ($M)": lo / 1e6, "NPV base ($M)": base / 1e6,
            "NPV at high ($M)": hi / 1e6, "Swing ($M)": abs(hi - lo) / 1e6,
        })
        lo = economics(route, price_overrides={}, capex_multiplier=1.0)
        for label, mult in [("Glycerol recovery -5 percentage points", 0.95)]:
            import copy
            r2 = copy.deepcopy(route)
            r2.glycerol_conversion *= mult
            alt = economics(r2)["NPV_$"]
            rows.append({
                "Variable": label, "Price key": "glycerol_conversion",
                "Low value": route.glycerol_conversion * mult,
                "Base value": route.glycerol_conversion,
                "High value": route.glycerol_conversion,
                "Unit": "fraction", "Confidence": "estimate",
                "NPV at low ($M)": alt / 1e6, "NPV base ($M)": base / 1e6,
                "NPV at high ($M)": base / 1e6,
                "Swing ($M)": abs(base - alt) / 1e6,
            })
    return pd.DataFrame(rows).sort_values("Swing ($M)", ascending=False)


def breakevens(routes_by_code):
    """One-dimensional root finds: what value makes NPV exactly zero."""
    rows = []

    def solve(label, route, key, lo, hi, unit, note=""):
        def f(x):
            return economics(route, price_overrides={key: x})["NPV_$"]
        try:
            if f(lo) * f(hi) > 0:
                rows.append({"Route": route.code, "Variable": label,
                             "Breakeven value": np.nan, "Unit": unit,
                             "Base value": PRICES[key].base,
                             "Note": "No sign change in the searched interval - "
                                     "NPV does not reach zero anywhere in the "
                                     "plausible range. " + note})
                return
            x = brentq(f, lo, hi, xtol=1e-4)
            rows.append({"Route": route.code, "Variable": label,
                         "Breakeven value": x, "Unit": unit,
                         "Base value": PRICES[key].base, "Note": note})
        except Exception as exc:
            rows.append({"Route": route.code, "Variable": label,
                         "Breakeven value": np.nan, "Unit": unit,
                         "Base value": PRICES[key].base, "Note": f"{exc}"})

    for code in ["C1", "C2", "E1", "E3"]:
        r = routes_by_code[code]
        pk = r.product_price_key or "crude_glycerol"
        solve("Product price for NPV = 0", r, pk, -400.0, 6000.0, "$/t")
        solve("Disposal cost for NPV = 0", r, "crude_disposal_cost",
              0.0, 800.0, "$/t crude",
              "Above this disposal cost the route beats continuing to pay the "
              "hauler. Coupled to the feed netback inside economics().")
        solve("Natural gas price for NPV = 0", r, "natural_gas",
              0.0, 60.0, "$/MMBtu")

    # Capacity breakeven. On the positive-netback basis this was the decisive
    # number (~54,600 t/yr). On a liability basis NPV is typically positive at
    # the client's own 10,000 t/yr, so there is no root.
    def f_cap(cap):
        return economics(aggregation_route(cap))["NPV_$"]
    lo_npv, hi_npv = f_cap(10000.0), f_cap(200000.0)
    if lo_npv * hi_npv > 0:
        rows.append({
            "Route": "E3", "Variable": "MINIMUM ECONOMIC SCALE (NPV = 0)",
            "Breakeven value": np.nan, "Unit": "t/yr crude glycerol fed",
            "Base value": CRUDE_TPY,
            "Note": (
                f"No sign change between 10,000 t/yr (NPV ${lo_npv/1e6:,.2f}M) "
                f"and 200,000 t/yr (NPV ${hi_npv/1e6:,.2f}M). Minimum economic "
                f"scale does not exist on this basis: the flowsheet does not "
                f"cross zero from below."
            ),
        })
    else:
        try:
            cap_star = brentq(f_cap, 10000.0, 200000.0, xtol=1.0)
            rows.append({
                "Route": "E3", "Variable": "MINIMUM ECONOMIC SCALE (NPV = 0)",
                "Breakeven value": cap_star, "Unit": "t/yr crude glycerol fed",
                "Base value": CRUDE_TPY,
                "Note": f"The client has {CRUDE_TPY:,.0f} t/yr of its own crude.",
            })
        except Exception as exc:
            rows.append({"Route": "E3", "Variable": "Minimum economic scale",
                         "Breakeven value": np.nan, "Unit": "t/yr",
                         "Base value": CRUDE_TPY, "Note": str(exc)})

    return pd.DataFrame(rows)


def capacity_sweep():
    rows = []
    for cap in range(10000, 90001, 5000):
        e = economics(aggregation_route(float(cap)))
        rows.append({
            "Crude fed (t/yr)": cap,
            "Third-party crude required (t/yr)": max(0, cap - CRUDE_TPY),
            "Product (t/yr)": e["product_tpy"],
            "ISBL ($M)": e["ISBL_$"] / 1e6,
            "TCI ($M)": e["TCI_$"] / 1e6,
            "Unit capex ($/annual t crude)": e["TCI_$"] / cap,
            "Fixed opex ($M)": e["fixed_opex_$"] / 1e6,
            "Fixed opex ($/t crude)": e["fixed_opex_$"] / cap,
            "EBITDA ($M)": e["EBITDA_$"] / 1e6,
            "Margin ($/t crude)": e["margin_per_t_crude_$"],
            "NPV ($M)": e["NPV_$"] / 1e6,
            "IRR": e["IRR"],
        })
    return pd.DataFrame(rows)


def grade_ladder(results_by_code):
    """Brief Trap 6: optimise profit, not purity.

    The grade choice here is genuinely discrete - there are four traded tiers,
    not a continuum - so this is reported as a ladder rather than a smooth
    optimum. The point survives: the margin comparator and the NPV comparator
    rank the ladder in OPPOSITE directions.
    """
    ladder = [("A1", "Crude, 80%"), ("E1", "Feed grade, ~87.5%"),
              ("C1", "Technical, 99.5%"), ("C2", "USP/EP, 99.7%")]
    rows = []
    for code, grade in ladder:
        e = results_by_code[code]
        rows.append({
            "Grade": grade, "Code": code,
            "Product price ($/t)": e["product_price_$_t"] or PRICES["crude_disposal_cost"].base,
            "Margin ($/t crude fed)": e["margin_per_t_crude_$"],
            "TCI ($M)": e["TCI_$"] / 1e6,
            "NPV ($M)": e["NPV_$"] / 1e6,
            "IRR": e["IRR"],
        })
    return pd.DataFrame(rows)


def monte_carlo(route, n=20000, seed=7):
    """Triangular draws on every price that carries a range, plus capex.

    Reported alongside the tornado rather than instead of it: the tornado says
    which variable matters, the Monte Carlo says how often the answer is wrong.
    """
    rng = np.random.default_rng(seed)
    keys = [k for k, _ in TORNADO_VARS]
    draws = {k: rng.triangular(PRICES[k].low, PRICES[k].base, PRICES[k].high, n)
             for k in keys}
    capex_mult = rng.triangular(0.70, 1.0, 1.50, n)

    npvs = np.empty(n)
    for i in range(n):
        ov = {k: draws[k][i] for k in keys}
        npvs[i] = economics(route, price_overrides=ov,
                            capex_multiplier=capex_mult[i])["NPV_$"]
    return npvs


# ----------------------------------------------------------------------------
# Reference tables for the workbook
# ----------------------------------------------------------------------------

def price_register():
    rows = []
    for k, p in PRICES.items():
        rows.append({
            "Key": k, "Base": p.base, "Low": p.low, "High": p.high,
            "Unit": p.unit, "Confidence": p.confidence,
            "Source": p.source, "Date": p.date, "Note": p.note,
        })
    return pd.DataFrame(rows).sort_values(["Confidence", "Key"])


def glycerine_history_table():
    rows = []
    for label, date, usp, tech, crude in GLYCERINE_HISTORY:
        rows.append({
            "Source": label, "Date": date,
            "USP veg 99.7% (c/lb)": usp, "Technical 99.5% (c/lb)": tech,
            "Crude 80% (c/lb)": crude,
            "USP ($/t)": usp * CENTS_LB_TO_USD_T,
            "Technical ($/t)": tech * CENTS_LB_TO_USD_T,
            "Crude ($/t)": crude * CENTS_LB_TO_USD_T,
            "Technical - crude spread ($/t)": (tech - crude) * CENTS_LB_TO_USD_T,
            "USP - technical premium ($/t)": (usp - tech) * CENTS_LB_TO_USD_T,
        })
    return pd.DataFrame(rows)


def capex_detail(results):
    rows = []
    for e in results:
        for line in e["_capex_lines"]:
            rows.append({"Code": e["code"], "Route": e["name"], **line})
    return pd.DataFrame(rows)


def stream_detail(results):
    rows = []
    for e in results:
        for line in e["_credit_lines"]:
            rows.append({"Code": e["code"], "Type": "Credit", **line})
        for line in e["_purchased_lines"]:
            rows.append({"Code": e["code"], "Type": "Purchased / disposal", **line})
    return pd.DataFrame(rows)


def cash_flow_detail(results_by_code, codes):
    rows = []
    for c in codes:
        e = results_by_code[c]
        for d in e["_cash_flow_detail"]:
            rows.append({"Code": c, **d})
    return pd.DataFrame(rows)


def opex_detail(results_by_code, codes):
    rows = []
    for c in codes:
        e = results_by_code[c]
        rows.append({
            "Code": c, "Route": e["name"],
            "Feed cost ($)": e["feed_cost_$"],
            "Purchased materials ($)": e["purchased_materials_$"],
            "Natural gas ($)": e["natural_gas_$"],
            "Electricity ($)": e["electricity_$"],
            "Cooling water ($)": e["cooling_water_$"],
            "Wastewater ($)": e["wastewater_$"],
            "VARIABLE OPEX ($)": e["variable_opex_$"],
            "Operators (FTE)": e["n_operators"],
            "Labour ($)": e["labor_$"],
            "Supervision ($)": e["supervision_$"],
            "Maintenance ($)": e["maintenance_$"],
            "Overhead ($)": e["overhead_$"],
            "Insurance and property tax ($)": e["insurance_tax_$"],
            "Other fixed ($)": e["extra_fixed_opex_$"],
            "FIXED OPEX ($)": e["fixed_opex_$"],
            "Product revenue ($)": e["product_revenue_$"],
            "Credit revenue ($)": e["credit_revenue_$"],
            "TOTAL REVENUE ($)": e["total_revenue_$"],
            "EBITDA ($)": e["EBITDA_$"],
        })
    return pd.DataFrame(rows)


def basis_table():
    rows = [{"Item": k, "Value": v, "Unit": "t/yr"} for k, v in FEED_TPY.items()]
    rows += [
        {"Item": "Total crude", "Value": CRUDE_TPY, "Unit": "t/yr"},
        {"Item": "Stranding barrier", "Value": STRANDING_BARRIER,
         "Unit": "methanol | quality | unresolved"},
        {"Item": "Crude disposal cost (invoiced)",
         "Value": PRICES["crude_disposal_cost"].base, "Unit": "$/t"},
        {"Item": "Client crude netback",
         "Value": PRICES["crude_glycerol"].base, "Unit": "$/t (negative)"},
        {"Item": "Merchant crude (third-party)",
         "Value": PRICES["merchant_crude_glycerol"].base, "Unit": "$/t"},
        {"Item": "Operating hours", "Value": 8000, "Unit": "h/yr"},
        {"Item": "CEPCI (current)", "Value": CEPCI_CURRENT, "Unit": "index"},
        {"Item": "CEPCI source", "Value": CEPCI_SOURCE, "Unit": ""},
        {"Item": "Discount rate", "Value": FIN.discount_rate, "Unit": "fraction"},
        {"Item": "Discount rate justification",
         "Value": DISCOUNT_RATE_JUSTIFICATION.strip(), "Unit": ""},
        {"Item": "Project life", "Value": FIN.project_life_years, "Unit": "yr"},
        {"Item": "Construction period", "Value": FIN.construction_years, "Unit": "yr"},
        {"Item": "Tax rate", "Value": FIN.tax_rate, "Unit": "fraction"},
        {"Item": "Depreciation", "Value": f"MACRS {FIN.macrs_class}-year. {MACRS_NOTE}",
         "Unit": ""},
        {"Item": "Working capital", "Value": FIN.working_capital_frac_fci,
         "Unit": "fraction of FCI"},
        {"Item": "Maintenance", "Value": FIN.maintenance_frac_fci,
         "Unit": "fraction of FCI"},
        {"Item": "Insurance and property tax", "Value": FIN.insurance_tax_frac_fci,
         "Unit": "fraction of FCI"},
        {"Item": "Supervision", "Value": FIN.supervision_frac_labor,
         "Unit": "fraction of labour"},
        {"Item": "Plant overhead", "Value": FIN.overhead_frac_labor_maint,
         "Unit": "fraction of labour + maintenance"},
        {"Item": "Shifts per position", "Value": FIN.shifts_per_position,
         "Unit": "FTE per position for 24/7 cover"},
        {"Item": "Contingency", "Value": FIN.contingency_frac,
         "Unit": "fraction of direct cost"},
        {"Item": "Owner's cost", "Value": FIN.owners_cost_frac, "Unit": "fraction of FCI"},
        {"Item": "Capex accuracy", "Value": CAPEX_ACCURACY, "Unit": ""},
        {"Item": "Feed transfer price convention",
         "Value": FIN.feed_transfer_price_convention, "Unit": ""},
    ]
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
    routes = build_routes()
    by_code = {r.code: r for r in routes}
    results = [economics(r) for r in routes]
    res_by_code = {e["code"]: e for e in results}

    a1 = res_by_code["A1"]
    disp = PRICES["crude_disposal_cost"].base
    net = PRICES["crude_glycerol"].base
    if abs(net + disp) > 1e-9:
        raise RuntimeError(
            f"A1 identity broken at the price register: netback {net} != "
            f"-disposal {disp}. The Pass-2 comparator is meaningless if these drift."
        )
    if abs(a1["EBITDA_$"]) > 1.0 or abs(a1["NPV_$"]) > 1.0:
        raise RuntimeError(
            f"A1 is the hurdle and must score zero; got EBITDA ${a1['EBITDA_$']:,.0f}, "
            f"NPV ${a1['NPV_$']:,.0f}."
        )

    p1 = pass1_table(routes)
    p2 = pass2_table(results)
    sweep = capacity_sweep()
    be = breakevens(by_code)
    ladder = grade_ladder(res_by_code)

    tor_e3 = tornado(by_code["E3"])
    tor_c1 = tornado(by_code["C1"])

    # Zero-feed-cost sensitivity, required by Brief Section 6
    zero_feed = pd.DataFrame([{
        "Code": e["code"], "Route": e["name"],
        "NPV, feed charged at netback ($M)": e["NPV_$"] / 1e6,
        "NPV, avoided-disposal credit removed ($M)":
            economics(by_code[e["code"]], charge_feed=False)["NPV_$"] / 1e6,
    } for e in results if e["gates_passed"] or e["product_tpy"] > 0])

    mc = monte_carlo(by_code["E3"], n=6000)
    mc_c1 = monte_carlo(by_code["C1"], n=6000)
    mc_tab = pd.DataFrame([
        {"Route": "E3 (30,000 t/yr aggregation)",
         "P(NPV > 0)": float((mc > 0).mean()),
         "P10 NPV ($M)": float(np.percentile(mc, 10)) / 1e6,
         "Median NPV ($M)": float(np.median(mc)) / 1e6,
         "P90 NPV ($M)": float(np.percentile(mc, 90)) / 1e6},
        {"Route": "C1 (10,000 t/yr stand-alone)",
         "P(NPV > 0)": float((mc_c1 > 0).mean()),
         "P10 NPV ($M)": float(np.percentile(mc_c1, 10)) / 1e6,
         "Median NPV ($M)": float(np.median(mc_c1)) / 1e6,
         "P90 NPV ($M)": float(np.percentile(mc_c1, 90)) / 1e6},
    ])

    path = os.path.join(OUT, "glycerol_TEA.xlsx")
    sheets = [
        ("01 Basis and conventions", basis_table()),
        ("02 Price register", price_register()),
        ("03 Glycerine price history", glycerine_history_table()),
        ("04 Pass 1 gates", p1),
        ("05 Pass 2 screen", p2),
        ("06 Finalist opex build-up", opex_detail(res_by_code, FINALISTS)),
        ("07 Capex build-up", capex_detail([res_by_code[c] for c in FINALISTS])),
        ("08 Stream detail", stream_detail([res_by_code[c] for c in FINALISTS])),
        ("09 Cash flows", cash_flow_detail(res_by_code, FINALISTS)),
        ("10 Capacity sweep", sweep),
        ("11 Breakevens", be),
        ("12 Tornado E3", tor_e3),
        ("13 Tornado C1", tor_c1),
        ("14 Grade ladder", ladder),
        ("15 Zero feed cost case", zero_feed),
        ("16 Monte Carlo", mc_tab),
    ]
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        for name, df in sheets:
            df.to_excel(xl, sheet_name=name, index=False)

    _print_console(p1, p2, sweep, be, ladder, tor_e3, mc_tab, zero_feed, res_by_code)
    print(f"\nWorkbook written to {path}")
    return dict(p1=p1, p2=p2, sweep=sweep, be=be, ladder=ladder,
                tornado_e3=tor_e3, tornado_c1=tor_c1, mc=mc_tab,
                zero_feed=zero_feed, results=res_by_code)


def _print_console(p1, p2, sweep, be, ladder, tor, mc, zero_feed, res):
    pd.set_option("display.width", 200, "display.max_columns", 40)
    print("=" * 100)
    print("PASS 1 - GATES")
    print("=" * 100)
    print(p1[["Code", "Route", "Result", "Failed gate(s)"]].to_string(index=False))

    print("\n" + "=" * 100)
    print("PASS 2 - COARSE ECONOMICS, RANKED BY MARGIN PER TONNE OF CRUDE FED")
    print("=" * 100)
    cols = ["Code", "Route", "Gate", "Crude fed (t/yr)", "Product (t/yr)",
            "EBITDA ($M)", "MARGIN $/t crude fed", "TCI ($M)", "NPV @12% ($M)", "IRR"]
    print(p2[cols].to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

    print("\n" + "=" * 100)
    print("CAPACITY SWEEP - the decisive analysis")
    print("=" * 100)
    print(sweep[["Crude fed (t/yr)", "Third-party crude required (t/yr)",
                 "TCI ($M)", "Unit capex ($/annual t crude)",
                 "Fixed opex ($/t crude)", "Margin ($/t crude)",
                 "NPV ($M)", "IRR"]].to_string(
        index=False, float_format=lambda x: f"{x:,.2f}"))

    print("\n" + "=" * 100)
    print("BREAKEVENS")
    print("=" * 100)
    print(be.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))

    print("\n" + "=" * 100)
    print("GRADE LADDER (Trap 6)")
    print("=" * 100)
    print(ladder.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

    print("\n" + "=" * 100)
    print("TORNADO - recommended route")
    print("=" * 100)
    print(tor[["Variable", "Low value", "Base value", "High value",
               "NPV at low ($M)", "NPV at high ($M)", "Swing ($M)",
               "Confidence"]].to_string(
        index=False, float_format=lambda x: f"{x:,.2f}"))

    print("\n" + "=" * 100)
    print("MONTE CARLO / ZERO-FEED-COST")
    print("=" * 100)
    print(mc.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
    print()
    print(zero_feed.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))


if __name__ == "__main__":
    main()
