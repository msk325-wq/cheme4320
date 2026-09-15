# Crude Glycerol Valorization — Stage 1 TEA

Route screening and ROI model for 10,000 t/yr of crude glycerol at a biodiesel
plant. Task brief in `glycerol-roi-optimization-brief.md`; recommendation in
**`glycerol-route-recommendation.md`**.

## Answer in one line

**On this branch the stream is a liability, not a byproduct.** The client
already pays $2.0M/yr ($200/t) to dispose of 10,000 t/yr of crude glycerol, so
the A1 hurdle is "keep paying the hauler" rather than "keep selling crude."
Merchant crude is still +$400/t (the stranding is client-specific); every route
that consumes the client's own crude is credited the avoided disposal cost.
Working notes in `glycerol-negative-netback-basis-change.md`. The committed
recommendation in `glycerol-route-recommendation.md` is the *previous* (positive
netback) basis and has not been rewritten yet.

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

Crude glycerol is charged to every route at its A1 netback, which on this branch
is **negative** (derived as −1 × the invoiced disposal cost). Route **A1
(dispose) still scores exactly zero margin by construction** and remains the
hurdle. A case with the avoided-disposal credit removed is reported separately.
