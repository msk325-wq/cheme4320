"""
One economic model, applied identically to every route.

Deliberately not an optimiser (Brief Section 9): route selection is a discrete,
structurally heterogeneous enumeration, capacity is pinned at a corner by the
design basis, and the 0.6-power capex law makes the objective non-convex anyway.
This module evaluates; routes.py enumerates.

Every intermediate is returned in the result dict so that a reviewer can
reproduce any headline number by hand.
"""

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import numpy_financial as npf

from .params import (
    CRUDE_TPY, PRICES, CEPCI, CEPCI_CURRENT, FIN, MACRS,
)


# ----------------------------------------------------------------------------
# Route description primitives
# ----------------------------------------------------------------------------

@dataclass
class CapexItem:
    """One scaled capital cost block.

    Scaled with the six-tenths rule from a referenced basis plant and escalated
    to the current CEPCI:

        C = C_basis * (S / S_basis)^n * (CEPCI_now / CEPCI_basis)

    `cost` must be an INSTALLED (battery-limits) cost, not bare equipment.
    """
    name: str
    basis_cost: float        # $ at basis capacity, in basis-year dollars
    basis_capacity: float    # capacity units matching `capacity`
    capacity: float          # this project's capacity in the same units
    exponent: float
    cepci_year: int
    capacity_unit: str
    source: str

    def scaled(self) -> float:
        scale = (self.capacity / self.basis_capacity) ** self.exponent
        escalation = CEPCI_CURRENT / CEPCI[self.cepci_year]
        return self.basis_cost * scale * escalation

    def breakdown(self) -> dict:
        scale = (self.capacity / self.basis_capacity) ** self.exponent
        escalation = CEPCI_CURRENT / CEPCI[self.cepci_year]
        return {
            "item": self.name,
            "basis_cost_$": self.basis_cost,
            "basis_capacity": self.basis_capacity,
            "project_capacity": self.capacity,
            "capacity_unit": self.capacity_unit,
            "exponent": self.exponent,
            "scale_factor": scale,
            "cepci_basis_year": self.cepci_year,
            "cepci_escalation": escalation,
            "scaled_installed_cost_$": self.basis_cost * scale * escalation,
            "source": self.source,
        }


@dataclass
class Stream:
    """A revenue credit or a purchased input.

    `quantity` is in the unit of the referenced price. Sign convention: positive
    quantity on a credit is income; positive quantity on a cost is expenditure.
    A price that is itself negative (e.g. salt disposal) flips automatically.
    """
    name: str
    quantity: float
    price_key: str
    basis: str = ""

    def value(self, price_overrides: Optional[dict] = None) -> float:
        p = _price(self.price_key, price_overrides)
        return self.quantity * p


def _price(key: str, overrides: Optional[dict] = None) -> float:
    if overrides and key in overrides:
        return overrides[key]
    return PRICES[key].base


@dataclass
class Route:
    code: str
    name: str
    category: str
    description: str = ""

    # --- Pass 1 gates -------------------------------------------------------
    gate_technical_readiness: str = "pass"
    gate_scale_fit: str = "pass"
    gate_raw_material: str = "pass"
    gate_safety_permitting: str = "pass"
    gate_chemcad: str = "pass"
    gate_feed_tolerance: str = "pass"
    gate_note: str = ""

    # --- Mass balance -------------------------------------------------------
    # crude_fed_tpy is the denominator of the Pass-2 comparator. It equals the
    # client's own 10,000 t/yr for every route EXCEPT the aggregation variant
    # E3, which deliberately processes third-party crude as well; dividing that
    # route's margin by 10,000 would flatter it by 3x.
    crude_fed_tpy: float = CRUDE_TPY
    glycerol_fed_tpy: float = 0.0
    glycerol_conversion: float = 1.0     # fraction of glycerol reacted/recovered
    selectivity: float = 1.0             # fraction of converted going to product
    mass_yield_ratio: float = 1.0        # t product per t glycerol at 100%/100%
    product_name: str = ""
    product_price_key: str = ""
    product_purity: float = 1.0
    freight_applies: bool = True

    # --- Economics ----------------------------------------------------------
    credits: List[Stream] = field(default_factory=list)
    purchased: List[Stream] = field(default_factory=list)
    gas_mmbtu_yr: float = 0.0
    elec_kwh_yr: float = 0.0
    cooling_water_m3_yr: float = 0.0
    wastewater_m3_yr: float = 0.0

    capex_items: List[CapexItem] = field(default_factory=list)
    operators_per_shift: float = 0.0
    extra_fixed_opex: float = 0.0
    extra_fixed_opex_note: str = ""
    osbl_frac_isbl: float = 0.30

    # Revenue multiplier by operating year, for qualification ramps etc.
    revenue_ramp: Optional[List[float]] = None
    ramp_note: str = ""

    charge_feed: bool = True

    @property
    def gates_passed(self) -> bool:
        return all(
            g == "pass" for g in [
                self.gate_technical_readiness, self.gate_scale_fit,
                self.gate_raw_material, self.gate_safety_permitting,
                self.gate_chemcad, self.gate_feed_tolerance,
            ]
        )

    @property
    def failed_gates(self) -> List[str]:
        names = {
            "technical readiness": self.gate_technical_readiness,
            "scale fit": self.gate_scale_fit,
            "raw material": self.gate_raw_material,
            "safety/permitting": self.gate_safety_permitting,
            "CHEMCAD": self.gate_chemcad,
            "feed tolerance": self.gate_feed_tolerance,
        }
        return [k for k, v in names.items() if v != "pass"]

    def product_tpy(self) -> float:
        """Sellable product tonnage.

        glycerol fed x conversion x selectivity x stoichiometric mass ratio,
        then divided by product purity to get as-sold tonnage.
        """
        reacted = self.glycerol_fed_tpy * self.glycerol_conversion
        to_product = reacted * self.selectivity * self.mass_yield_ratio
        return to_product / self.product_purity if self.product_purity else 0.0


# ----------------------------------------------------------------------------
# The economic model
# ----------------------------------------------------------------------------

def economics(route: Route,
              fin=FIN,
              price_overrides: Optional[dict] = None,
              capex_multiplier: float = 1.0,
              charge_feed: Optional[bool] = None) -> dict:
    """Evaluate one route. Returns every intermediate, not just headlines."""

    po = dict(price_overrides or {})
    # Keep the A1 identity: netback == -disposal_cost. A tornado or Monte Carlo
    # draw that moves one without the other would make the baseline stop netting
    # to zero, which silently breaks the Pass-2 comparator.
    if "crude_disposal_cost" in po:
        po["crude_glycerol"] = -po["crude_disposal_cost"]
    elif "crude_glycerol" in po:
        po["crude_disposal_cost"] = -po["crude_glycerol"]
    charge = route.charge_feed if charge_feed is None else charge_feed

    # ---- Revenue ----------------------------------------------------------
    prod_tpy = route.product_tpy()
    prod_price = _price(route.product_price_key, po) if route.product_price_key else 0.0
    freight = _price("freight_out", po) if route.freight_applies else 0.0
    net_prod_price = prod_price - freight
    product_revenue = prod_tpy * net_prod_price

    credit_lines = [
        {"name": c.name, "quantity": c.quantity, "price_key": c.price_key,
         "unit_price": _price(c.price_key, po), "value_$": c.value(po),
         "basis": c.basis}
        for c in route.credits
    ]
    credit_revenue = sum(c["value_$"] for c in credit_lines)
    total_revenue = product_revenue + credit_revenue

    # ---- Variable operating cost -----------------------------------------
    feed_price = _price("crude_glycerol", po)
    feed_cost = CRUDE_TPY * feed_price if charge else 0.0

    purchased_lines = [
        {"name": p.name, "quantity": p.quantity, "price_key": p.price_key,
         "unit_price": _price(p.price_key, po), "value_$": p.value(po),
         "basis": p.basis}
        for p in route.purchased
    ]
    purchased_cost = sum(p["value_$"] for p in purchased_lines)

    gas_cost = route.gas_mmbtu_yr * _price("natural_gas", po)
    elec_cost = route.elec_kwh_yr * _price("electricity", po)
    cw_cost = route.cooling_water_m3_yr * _price("cooling_water", po)
    ww_cost = route.wastewater_m3_yr * _price("wastewater", po)
    utilities_cost = gas_cost + elec_cost + cw_cost + ww_cost

    variable_opex = feed_cost + purchased_cost + utilities_cost

    # ---- Capital ----------------------------------------------------------
    capex_lines = [c.breakdown() for c in route.capex_items]
    isbl = sum(c["scaled_installed_cost_$"] for c in capex_lines) * capex_multiplier
    osbl = isbl * route.osbl_frac_isbl
    direct = isbl + osbl
    contingency = direct * fin.contingency_frac
    fci = direct + contingency
    owners_cost = fci * fin.owners_cost_frac
    working_capital = fci * fin.working_capital_frac_fci
    tci = fci + owners_cost + working_capital
    depreciable_base = fci + owners_cost

    # ---- Fixed operating cost --------------------------------------------
    op_rate = _price("operator_burdened", po)
    n_operators = route.operators_per_shift * fin.shifts_per_position
    labor = n_operators * op_rate
    supervision = labor * fin.supervision_frac_labor
    maintenance = fci * fin.maintenance_frac_fci
    overhead = (labor + supervision + maintenance) * fin.overhead_frac_labor_maint
    insurance_tax = fci * fin.insurance_tax_frac_fci
    fixed_opex = (labor + supervision + maintenance + overhead
                  + insurance_tax + route.extra_fixed_opex)

    # ---- Margin (the Pass-2 comparator) ----------------------------------
    ebitda = total_revenue - variable_opex - fixed_opex
    margin_per_t_crude = ebitda / route.crude_fed_tpy

    # ---- Cash flow, NPV, IRR ---------------------------------------------
    cf, detail = _cash_flows(ebitda, tci, fci, owners_cost, working_capital,
                             depreciable_base, fin, route, product_revenue)

    npv = npf.npv(fin.discount_rate, cf)
    try:
        irr = npf.irr(cf)
        if irr is not None and (np.isnan(irr) or np.isinf(irr)):
            irr = None
    except Exception:
        irr = None

    op_years = [d for d in detail if d["phase"] == "operating"]
    avg_net_profit = float(np.mean([d["net_income"] for d in op_years])) if op_years else 0.0
    avg_cash_flow = float(np.mean([d["cash_flow"] for d in op_years])) if op_years else 0.0

    simple_roi = avg_net_profit / tci if tci > 0 else float("nan")
    payback = _payback(cf, fin.construction_years)

    return {
        "code": route.code,
        "name": route.name,
        "category": route.category,
        "gates_passed": route.gates_passed,
        "failed_gates": ", ".join(route.failed_gates),
        "gate_note": route.gate_note,

        # mass balance
        "crude_fed_tpy": route.crude_fed_tpy,
        "glycerol_fed_tpy": route.glycerol_fed_tpy,
        "glycerol_conversion": route.glycerol_conversion,
        "selectivity": route.selectivity,
        "mass_yield_ratio": route.mass_yield_ratio,
        "product": route.product_name,
        "product_tpy": prod_tpy,
        "product_price_$_t": prod_price,
        "freight_$_t": freight,
        "net_product_price_$_t": net_prod_price,

        # revenue
        "product_revenue_$": product_revenue,
        "credit_revenue_$": credit_revenue,
        "total_revenue_$": total_revenue,

        # variable opex
        "feed_cost_$": feed_cost,
        "purchased_materials_$": purchased_cost,
        "natural_gas_$": gas_cost,
        "electricity_$": elec_cost,
        "cooling_water_$": cw_cost,
        "wastewater_$": ww_cost,
        "utilities_total_$": utilities_cost,
        "variable_opex_$": variable_opex,

        # capital
        "ISBL_$": isbl,
        "OSBL_$": osbl,
        "contingency_$": contingency,
        "FCI_$": fci,
        "owners_cost_$": owners_cost,
        "working_capital_$": working_capital,
        "TCI_$": tci,

        # fixed opex
        "n_operators": n_operators,
        "labor_$": labor,
        "supervision_$": supervision,
        "maintenance_$": maintenance,
        "overhead_$": overhead,
        "insurance_tax_$": insurance_tax,
        "extra_fixed_opex_$": route.extra_fixed_opex,
        "fixed_opex_$": fixed_opex,

        # headline
        "EBITDA_$": ebitda,
        "margin_per_t_crude_$": margin_per_t_crude,
        "avg_net_profit_$": avg_net_profit,
        "avg_cash_flow_$": avg_cash_flow,
        "simple_ROI": simple_roi,
        "payback_years": payback,
        "NPV_$": npv,
        "IRR": irr,

        # traceability
        "_capex_lines": capex_lines,
        "_credit_lines": credit_lines,
        "_purchased_lines": purchased_lines,
        "_cash_flows": cf,
        "_cash_flow_detail": detail,
        "_route": route,
    }


def _cash_flows(ebitda, tci, fci, owners_cost, working_capital,
                depreciable_base, fin, route, product_revenue):
    """Build the year-by-year after-tax cash flow series.

    Year 0..(construction_years-1): capital spend, no operations.
    Working capital is injected in the final construction year and recovered in
    the final operating year. Depreciation is MACRS on FCI + owner's cost.
    """
    spend_profile = ([0.40, 0.60] if fin.construction_years == 2
                     else [1.0 / fin.construction_years] * fin.construction_years)
    macrs = MACRS[fin.macrs_class]

    cf, detail = [], []

    for y in range(fin.construction_years):
        capital = (fci + owners_cost) * spend_profile[y]
        wc = working_capital if y == fin.construction_years - 1 else 0.0
        flow = -(capital + wc)
        cf.append(flow)
        detail.append({
            "year": y, "phase": "construction", "capital_spend": capital,
            "working_capital": wc, "ebitda": 0.0, "depreciation": 0.0,
            "taxable_income": 0.0, "tax": 0.0, "net_income": 0.0,
            "cash_flow": flow,
        })

    ramp = route.revenue_ramp or [1.0] * fin.project_life_years
    for i in range(fin.project_life_years):
        y = fin.construction_years + i
        mult = ramp[i] if i < len(ramp) else 1.0
        # Ramp scales product revenue only; credits and costs are unaffected.
        yr_ebitda = ebitda - product_revenue * (1.0 - mult)

        dep = depreciable_base * macrs[i] if i < len(macrs) else 0.0
        taxable = yr_ebitda - dep
        tax = max(0.0, taxable) * fin.tax_rate
        net_income = taxable - tax
        wc_recovery = working_capital if i == fin.project_life_years - 1 else 0.0
        salvage = fci * fin.salvage_frac_fci if i == fin.project_life_years - 1 else 0.0
        flow = net_income + dep + wc_recovery + salvage

        cf.append(flow)
        detail.append({
            "year": y, "phase": "operating", "capital_spend": 0.0,
            "working_capital": -wc_recovery, "revenue_multiplier": mult,
            "ebitda": yr_ebitda, "depreciation": dep, "taxable_income": taxable,
            "tax": tax, "net_income": net_income, "cash_flow": flow,
        })

    return cf, detail


def _payback(cf, construction_years):
    """Years from start of operations until cumulative cash flow turns positive."""
    cum = np.cumsum(cf)
    for i, c in enumerate(cum):
        if c >= 0:
            if i == 0:
                return 0.0
            prev = cum[i - 1]
            frac = -prev / (c - prev) if (c - prev) != 0 else 0.0
            return (i - 1 + frac) - (construction_years - 1)
    return float("inf")
