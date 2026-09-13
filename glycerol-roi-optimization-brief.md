# Crude Glycerol Valorization — Route Selection & ROI Optimization Brief

**Use:** paste this file into a fresh Claude conversation as the task brief.
**Project:** Olin Engineering (consultant) → Cayuga Renewable Fuels (client). Stage 1 deliverable: feasibility screening and route recommendation, with enough economic depth to defend the pick.

---

## 1. Your role and the question

You are the lead process/TEA engineer on a consulting engagement. A biodiesel producer has a crude glycerol byproduct stream and wants to know the single highest-ROI thing to do with it.

**The question is explicitly not "how do I purify glycerol."** It is: *given this stream at our battery limits, where in the value chain should we sit, and what should we build?* Every position is on the table:

- **Do nothing new** — sell crude as-is to a merchant refiner (this is the null hypothesis and the baseline every other option must beat)
- **Upstream-adjacent / internal** — burn it, reform it, or otherwise use it to displace a purchased input at the biodiesel plant
- **Midstream** — purify to technical, refined, or USP/EP grade and sell as a commodity
- **Downstream** — convert to a derivative chemical or formulated product and sell into a specialty market
- **Hybrid / staged** — e.g. modest purification now, conversion capacity added later; or a slate where one route takes the main glycerol cut and a second monetizes a side stream

Do not assume the answer. Screen the space, then commit to a recommendation with a number behind it.

---

## 2. Design basis (fixed — do not redesign upstream)

The stream is delivered to the battery limits at the stated condition. You do not get to change the biodiesel plant to give you a cleaner or different feed.

### Table 1 — Crude glycerol feed specification

| Component | Notes | Composition (wt %) | Flow (kg/h) |
|---|---|---|---|
| Glycerol | Primary species | 80.0 | 1,000 |
| Methanol | Recoverable; from transesterification | 9.0 | 112.5 |
| Water | From washing / reaction | 5.0 | 62.5 |
| Residual FAME | Unconverted biodiesel | 3.0 | 37.5 |
| Soaps | Fatty-acid salts | 1.5 | 18.75 |
| Salts / catalyst residue | Inorganic ash | 1.5 | 18.75 |
| **Total** | | **100.0** | **1,250** |

### Derived annual basis (8,000 h/yr)

| Component | t/yr |
|---|---|
| Glycerol | 8,000 |
| Methanol | 900 |
| Water | 500 |
| Residual FAME | 300 |
| Soaps | 150 |
| Salts / ash | 150 |
| **Total crude** | **10,000** |

**Assume unless told otherwise (and state these as assumptions):**
- Feed is homogeneous, continuous, and available every one of the 8,000 h
- Ambient-ish delivery condition; if you need a specific T/P for design, state your assumption
- Alkali-catalyzed (NaOH/KOH/methoxide) biodiesel process implied by the soap + ash profile. The identity of the cation matters for salt disposal vs. K-salt fertilizer credit — flag it as a decision-relevant unknown and carry both cases if it changes the ranking.
- Feedstock oil type is unspecified; it affects FFA/FAME chain length and any downstream fatty-acid credit. Flag as an assumption.

### Non-negotiable constraints

- Scale is what it is: ~10,000 t/yr crude in. No importing third-party glycerol to build scale **unless** you explicitly propose it as a variant, size the merchant supply, and defend feedstock availability and price risk.
- Process design in the later stage must be CHEMCAD-modelable. Prefer routes with tractable thermodynamics and available component data. If a route needs custom kinetics, non-database components, or biological reactors CHEMCAD handles poorly, **say so now** — that is a real selection criterion for this project, not a footnote.
- Recommendation must be buildable by a mid-size producer, not a chemical major. No routes that only work with captive downstream integration the client doesn't have.

---

## 3. The central tension — engage with it head-on

**1,000 kg/h of glycerol is roughly 1 tonne per hour.** In commodity chemicals this is a rounding error. World-scale epichlorohydrin, propylene glycol, and acrylic acid plants are 50,000–300,000 t/yr. At 8,000 t/yr of glycerol feed, a commodity conversion route carries the full complexity and fixed-cost burden of a chemical plant while selling into a market priced by assets 20× larger with 20× better unit economics.

This cuts both ways and you must reason through it rather than reflexively picking small:

- **Against conversion:** capex scales roughly to the 0.6–0.7 power, so unit capex at 8,000 t/yr is ~3–4× a world-scale plant's. Fixed opex (operators, maintenance, overhead, insurance) barely scales down at all and can swamp a small plant. Commodity price is set by the marginal world-scale producer.
- **For conversion:** margin per tonne on a specialty derivative can be 5–20× the margin on refined glycerol, and small-volume specialty markets (cosmetics intermediates, fuel additives, niche solvents) are *not* priced by world-scale assets. A 2,000 t/yr product at $4,000/t generates more gross profit than 7,500 t/yr of refined glycerol at $700/t.
- **For purification:** far lower capex, mature and de-risked technology, straightforward CHEMCAD model, fast payback — but you are a price-taker in a market with heavy low-cost import competition, and the spread between crude and refined glycerol is the entire business.

**Quantify this tension. Do not hand-wave it.** The recommendation should fall out of the numbers.

---

## 4. Route space to screen

Screen at minimum the following. Add anything you think is missing — this list is a floor, not a ceiling.

### A. Baseline / no-build
- **A1.** Sell crude glycerol as-is to a merchant refiner (establishes the opportunity cost of the feed — this is the number every route must beat)
- **A2.** Pay for disposal / anaerobic digestion offtake (downside case if crude markets go negative, which has happened)

### B. Energy / internal use
- **B1.** Combust for process steam at the biodiesel plant (displaces natural gas; watch acrolein emissions, ash slagging, and burner turndown)
- **B2.** Steam reforming or aqueous-phase reforming to hydrogen or syngas
- **B3.** Anaerobic digestion co-substrate → biogas / RNG (check RIN, LCFS, or RNG credit eligibility)

### C. Midstream — purification
- **C1.** Technical grade (~98%): acidulation → phase split → methanol recovery → evaporation → possibly short-path or wiped-film
- **C2.** Refined / USP-EP grade (99.5%+): C1 plus vacuum distillation, ion exchange or ion exclusion, activated-carbon bleaching, deodorization
- **C3.** Membrane or ion-exchange-led purification as an alternative to distillation (lower energy, higher consumables — worth a look at this scale)

### D. Downstream — conversion
- **D1.** Propylene glycol (1,2-PDO) via hydrogenolysis (Cu-Cr, Cu/ZnO, Ru); needs H₂ supply — price it honestly
- **D2.** 1,3-propanediol (fermentation, or catalytic); higher value, harder process, poor CHEMCAD fit
- **D3.** Epichlorohydrin via hydrochlorination (Epicerol-type); strong chemistry, but scale and HCl logistics are brutal
- **D4.** Acrolein → acrylic acid via dehydration/oxidation; acrolein toxicity and handling is a serious constraint
- **D5.** Glycerol carbonate (transesterification with dimethyl carbonate or urea); mild conditions, growing market
- **D6.** Solketal (ketalization with acetone) — fuel oxygenate / solvent; very mild process, low capex, modest value
- **D7.** Glycerol tert-butyl ethers (GTBE) — fuel additive; needs isobutylene
- **D8.** Dihydroxyacetone (DHA) via oxidation/fermentation — small volume, very high value (self-tanning / cosmetics); check whether market volume can even absorb your output
- **D9.** Lactic acid, succinic acid, or citric acid via fermentation
- **D10.** Polyglycerols and polyglycerol esters (emulsifiers, food and personal care) — moderate value, decent scale fit
- **D11.** Acetol / hydroxyacetone; allyl alcohol
- **D12.** Glycerol esters / triacetin (acetylation) — plasticizer, fuel additive, food

### E. Low-capex / formulated products
- **E1.** Animal feed grade (low purification, USDA/AAFCO constraints, methanol limits are the binding spec — verify them)
- **E2.** Dust suppressant, de-icer, or antifreeze blend component
- **E3.** Toll refining or contract purification for other regional biodiesel producers

### F. Side-stream monetization (stacks on top of any route above)
- **F1.** Methanol recovery and return to the biodiesel plant — 900 t/yr is real money and most routes need methanol gone anyway
- **F2.** FAME / free fatty acid recovery from acidulation top layer — 300 t/yr, sellable or returnable to the esterification step
- **F3.** Soap → FFA conversion via acidulation — another ~150 t/yr of fatty material
- **F4.** Salt cake — disposal cost, or a K₂SO₄ fertilizer credit if the catalyst was potassium-based

**Treat Section F as near-mandatory in every route you cost.** These credits and avoided costs often decide the ranking, and a route that ignores them will be mis-ranked.

---

## 5. Screening method

Work in three passes. Show your work at each pass.

### Pass 1 — Gates (pass/fail, fast)
Kill anything that fails one of these, and say why in one line:
- Technical readiness: is there a commercially demonstrated process, or is this a paper from 2019?
- Scale fit: can the target market absorb your output, and can you be cost-competitive at 1 t/h?
- Raw material dependency: does it require a co-reactant (H₂, HCl, isobutylene, DMC) the client can't reliably source at this scale?
- Safety / permitting: does it create a showstopper hazard or emissions burden for a mid-size producer?
- CHEMCAD tractability: can this actually be simulated and converged for Stage 2?
- Feed tolerance: can the chemistry survive the salts, soaps, and FAME, or does it require purification first (in which case the purification capex is part of the route's cost)?

### Pass 2 — Coarse economics (order-of-magnitude, all survivors)
For each surviving route, build a one-page economic sketch:
- Mass balance to product (glycerol conversion, selectivity, overall yield to sellable product)
- Revenue: product tonnage × price, plus all Section F credits
- Variable opex: co-reactants, catalyst, utilities, waste disposal
- Fixed opex: labor, maintenance, overhead, insurance
- Capex: factored estimate (Lang or Guthrie), scaled with an explicit six-tenths-rule exponent from a referenced basis plant, escalated to current CEPCI
- **Gross margin per tonne of crude glycerol fed** — use this as the common comparator across every route

Rank. Carry the top 3–4 forward.

### Pass 3 — Deep dive (top 3–4)
For each finalist:
- Block flow diagram with named unit operations, key T/P, and stream splits
- Capex build-up by major equipment item with basis and scaling source
- Full opex table
- Working capital estimate
- **ROI, defined explicitly.** Report all of:
  - Simple ROI = average annual net profit ÷ total capital investment
  - Payback period (years)
  - NPV at a stated discount rate (propose 10–12% and justify)
  - IRR
  - State your tax, depreciation (MACRS class), and project-life assumptions up front
- Sensitivity: tornado chart inputs over at least product price, glycerol feed cost/credit, capex accuracy (±30%), utility cost, and yield/selectivity
- Breakeven analysis: what product price, or what yield, makes this route indifferent to the baseline?
- Risk register: top 5 risks with mitigation

---

## 6. Economic ground rules

- **ROI headline metric:** simple ROI as defined above, but the recommendation must be defended on NPV and IRR too. If they disagree, explain why and which one should drive the decision.
- **Feed cost:** the crude glycerol is not free. Charge the project the market price it would otherwise fetch (option A1) as an internal transfer price, and run a sensitivity where it is free. Say which convention you used everywhere.
- **Capex accuracy:** target AACE Class 4/5 (−30%/+50%). State it. Use factored estimating, cite the basis, and escalate with CEPCI to the most recent index you can verify.
- **Prices:** every price must have a source and a date. Glycerol markets are violently cyclical and structurally tied to biodiesel and renewable diesel production volumes. Refined glycerol has been flooded by low-cost Asian and Argentine supply in recent years. **Do not assert a price from memory — search for it, cite it, and give a range rather than a point estimate.**
- **Honest uncertainty:** where you can't find a number, say so and use a clearly labeled placeholder with a plausible range. Do not fabricate a price, a yield, or a catalyst performance figure. A flagged gap is useful; an invented number is worse than nothing because it propagates silently into the ranking.

---

## 7. Traps to avoid

Design-project write-ups on this feed usually fail in the same places:

1. **Ignoring the salt.** Acidulation with H₂SO₄ converts soaps to FFA and precipitates Na₂SO₄ or K₂SO₄. That's hundreds of tonnes per year of salt cake with a real disposal cost — or a fertilizer credit if potassium. It is not zero either way.
2. **Under-costing methanol removal.** Methanol must come out first in essentially every route. It's also 900 t/yr of recoverable value. Both the cost and the credit belong in the model.
3. **Distillation fouling.** Glycerol's normal boiling point is ~290 °C and it thermally degrades near there. Vacuum operation is mandatory; residual salts foul reboilers and shorten runs. Thin-film or wiped-film evaporation exists for a reason. Don't spec a conventional 40-tray column at atmospheric pressure.
4. **Assuming USP grade = USP price.** USP/EP glycerin sells at a premium because of cGMP-adjacent quality systems, batch documentation, and multi-year customer qualification cycles — not just because of a purity number on a spec sheet. Model the commercial cost and time lag of getting qualified, or discount the price you assume.
5. **Forgetting that the client is a biodiesel producer.** Glycerol supply is correlated with biodiesel economics, which are policy-driven (RFS, RIN prices, blender's tax credit, LCFS). A route whose margin also depends on those same policies is doubly exposed. Note correlated risk rather than treating each variable as independent.
6. **Optimizing purity instead of profit.** Higher purity costs energy and capex non-linearly. The optimum is almost never "as pure as possible." Find the grade that maximizes margin, and show the curve.
7. **Yield optimism.** Lab selectivities do not survive contact with a real feed containing salts and soaps. Discount literature yields and say by how much and why.
8. **Skipping the null hypothesis.** If the answer is "just sell it crude and pocket the capex," that is a legitimate and defensible finding. Say so if the numbers say so.

---

## 8. Deliverable

Produce a single markdown document with:

1. **Executive summary** — the recommendation in the first three sentences, with headline ROI, NPV, IRR, payback, and capex. Then the one-sentence reason it beats the runner-up.
2. **Route screening matrix** — all candidates, gate results, coarse margin per tonne of crude fed, rank.
3. **Finalist deep dives** — 3–4 routes, per Section 5 Pass 3.
4. **Recommendation and defense** — why this one, what would change the answer, and under what conditions the runner-up wins.
5. **Sensitivity and risk** — tornado inputs, breakevens, top risks.
6. **Assumption register** — every assumption in one table, each tagged as (a) sourced, (b) engineering estimate, or (c) placeholder needing verification.
7. **Stage 2 readiness note** — for the recommended route: what CHEMCAD needs (thermo package recommendation, component availability, likely convergence pain points, which unit ops will need custom blocks or user-specified conversions).
8. **Source list** with dates.

Use tables for anything comparative. Show the arithmetic for every headline economic number — the grader will check it, and a number I can't reproduce is a number I can't defend in the report.

---

## 9. Computational approach

Build the screening model in **Python**. Do not reach for a convex optimizer — this is an enumeration-and-evaluation problem, not a search problem.

### Why not an optimizer

- **Route selection is discrete and structurally heterogeneous.** There is no continuous feasible set connecting "sell crude" to "build an epichlorohydrin plant." There are ~25 named alternatives to be evaluated consistently, not a space to be searched.
- **Capacity is already a corner solution.** Economies of scale push monotonically toward larger, and you are bounded at 8,000 t/yr of glycerol by the design basis. There is no interior optimum to find.
- **The cost model is non-convex anyway.** Capex scales as `C = C₀·(S/S₀)^0.6`, which is concave in S. Maximizing (linear revenue − concave cost) is maximization of a convex function — non-convex, and outside what CVXPY or any DCP-ruleset tool will accept. It would reject the formulation at parse time rather than mislead, but the effort would go into fighting the ruleset instead of into the engineering.

What is actually needed is one economic model applied 25 times with identical conventions.

### Recommended structure

```python
# numpy, pandas, numpy-financial, scipy
@dataclass
class Route:
    name: str
    glycerol_conversion: float
    selectivity: float
    product_price: float      # $/t, carry (low, base, high)
    coreactant_cost: float
    capex_base: tuple         # (cost, basis_capacity, exponent, CEPCI_year)
    ...

def economics(route, feed_tpy=8000, hours=8000) -> dict:
    # returns revenue, variable opex, fixed opex, capex,
    # ROI, NPV, IRR, payback — plus every intermediate
```

Then `pd.DataFrame([economics(r) for r in routes])` and sort on margin per tonne of crude fed. The whole Pass-2 screen should be on the order of 300 lines.

### Numerical pieces that do warrant a library

| Task | Tool |
|---|---|
| NPV, IRR | `numpy_financial.npv` / `.irr` — do not hand-roll IRR |
| Breakeven ("what price makes NPV zero") | `scipy.optimize.brentq`, 1-D root find |
| Within-route optimum (e.g. purity that maximizes margin, Trap 6) | `scipy.optimize.minimize_scalar`, one decision variable |
| Tornado / sensitivity | Plain sweeps — each input over its range, others at base. No library needed. |
| Monte Carlo, if distributions are wanted over a tornado | Pure NumPy, 10k draws, milliseconds at this size |

If a genuine constrained optimization with integer decisions appears later — a product slate splitting glycerol across two routes with shared utilities, say — use **Pyomo** with BONMIN or Couenne. It handles MINLP and non-convexity; CVXPY structurally cannot.

### Output requirement

Export the finished TEA to **.xlsx** (`openpyxl`) with intermediate columns intact, not just headline metrics. The economics must be traceable line by line: a reviewer needs to reproduce every number by hand, and a printed DataFrame with visible intermediates is defensible in a way a solver's optimal vector is not. Design-course reviewers generally expect spreadsheet-legible economics regardless of what generated them.

---

## 10. How to work

- Ask clarifying questions **only** if something genuinely blocks you. Otherwise state an assumption, flag it clearly, and proceed.
- Search for market prices, capex bases, and yield data rather than recalling them. Cite what you find.
- If your screening leads somewhere unexpected — a route not on the list in Section 4, or a conclusion that the null hypothesis wins — follow it and say so plainly. I want the right answer, not a confirmation of the list.
- Push back on anything in this brief that you think is wrong.
