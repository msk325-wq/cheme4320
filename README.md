# Crude Glycerol Valorization — Stage 1 TEA

Route screening and ROI model for 10,000 t/yr of crude glycerol at a biodiesel
plant. Task brief in `glycerol-roi-optimization-brief.md`; recommendation in
**`glycerol-route-recommendation.md`**.

## Answer in one line

Do not build. The recommendation is **A1 — keep selling crude glycerol as-is**.
Minimum economic scale for glycerol purification is **54,645 t/yr of crude**,
which is 5.5x the client's production and roughly 130% of the entire estimated
PADD 1 crude glycerol pool, so even regional aggregation cannot reach it: a
30,000 t/yr refinery returns NPV -$13.6M at IRR 5.1%. The one item worth
pursuing is a $3.5M methanol-recovery and feed-spec project (E1) at NPV -$0.7M,
IRR 7.8% — which turns positive on a $16/t move in a premium we could not
source, and is therefore a commercial diligence question, not an engineering
one.

## Run it

```bash
python3.13 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m tea.run       # screen, breakevens, sensitivity, workbook
./.venv/bin/python -m tea.figures   # charts
```

## Layout

| Path | Contents |
|---|---|
| `tea/params.py` | Design basis, price register (every price tagged `sourced` / `estimate` / `placeholder` with a source and date), CEPCI, financial conventions |
| `tea/model.py` | `Route` and `CapexItem` dataclasses and the single `economics()` function applied identically to every route |
| `tea/routes.py` | The 22 routes: Pass 1 gates and Pass 2 mass and energy balances, arithmetic written out inline |
| `tea/run.py` | Three-pass screen, capacity sweep, `brentq` breakevens, tornado, Monte Carlo, workbook export |
| `tea/figures.py` | Charts used in the report |
| `outputs/glycerol_TEA.xlsx` | 16-sheet traceable TEA with every intermediate column |
| `outputs/screen_console.txt` | Full console output of the last run |

## Method note

This is an enumeration, not an optimisation. Route selection is discrete and
structurally heterogeneous, capacity is pinned at a corner by the design basis,
and the 0.6-power capex law makes the objective non-convex — so the model is one
economic function applied 22 times under identical conventions. `scipy.optimize`
is used only for one-dimensional root finds (breakevens) and
`numpy_financial` for NPV and IRR.

Crude glycerol is charged to every route at its market netback, so route **A1
(sell as-is) scores exactly zero margin by construction** and is the hurdle every
other route must clear. A zero-feed-cost case is reported separately.
