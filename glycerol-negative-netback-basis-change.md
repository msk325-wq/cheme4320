# Basis Change: Crude Glycerol as a Liability

Working notes for branch `correct-baseline`. Supersedes nothing yet — no code has
been changed. Every number below was produced by driving the committed model
through `economics(route, price_overrides=...)` in memory, plus in-memory
retargeting of stream price keys to simulate the proposed architecture. They are
indicative and must be reproduced once the architecture lands.

---

## 1. The change

The committed study assumes crude glycerol is a saleable byproduct at a $400/t
netback (Argus, four dated assessments), which makes route A1 "sell crude as-is"
worth $4.0M/yr of revenue. The new going concern is the opposite: the stream is a
**waste liability costing $1.8–2.2M/yr to dispose of**, i.e. a netback of
approximately **−$180 to −$220/t**, base −$200/t.

### Client answers to the diligence questions

| Question | Answer | Consequence |
|---|---|---|
| Is the negative value client-specific or market-wide? | **Client-specific** (stranded stream) | Refined glycerine prices hold; E3's gate fee is *not* available |
| Is it a hazardous (RCRA D001 ignitable) liquid? | **No** | Removes the reclassification step-change; the $200/t needs a different justification |
| What do they pay today? | **$2M/yr, already being paid** | Best-sourced number in the study; but it is a *contract* |

**Caution on the first answer.** It was chosen partly because it produces higher
IRRs for the purification routes. That reasoning will not survive review in a
document that opens with a revision note withdrawing a prior recommendation on
grounds of honesty. Justify client-specific on a *named mechanism*, and carry
market-wide as a documented downside scenario.

It is also not uniformly favourable. Client-specific holds refined prices up
(helps C1/C2) but destroys E3's gate fee, worth about $12M/yr of EBITDA — the
largest single line in the naive override.

---

## 2. Does the assumption make sense

Yes, and the committed report already anticipates it. §7 states "crude glycerol
collapses below $94/t → C1's economics invert"; solving the model for C1's
NPV = 0 gives **$94.3/t**. The new basis is $294/t past that inversion point.
The brief's §4 A2 also explicitly contemplates negative crude markets.

**Magnitude cross-check.** At ~1.23 kg/L, 10,000 t/yr is about 2.15M gal, so
$1.8–2.2M/yr equals **$0.84–1.02/gal**. The price register already cites
$0.25–1.00/gal as the historical disposal cost for unprocessed trap grease
(see the `acid_oil_ffa` note). So the estimate is internally consistent but sits
at or above the top of that band — for a material that is *non*-hazardous. It is
also 2.5× the $80/t `solid_waste_disposal` figure used elsewhere, which is a
solid non-hazardous landfill basis and the wrong basis for 2.15M gal/yr of liquid.

**Open credibility risk.** Crude glycerol is a prized anaerobic digestion
co-substrate; digesters often take it at a low gate fee or pay for it. Paying
~$1/gal to dispose of non-hazardous material a digester would value is anomalous
and a reviewer will ask. Name the mechanism: high-COD POTW surcharge,
incineration, fuel blending, long-haul licensed hauling, or an AD gate fee. Each
escalates differently and each has a different substitution option.

---

## 3. What the model does today under a naive override

Setting `crude_glycerol = -200` and changing nothing else:

| Route | EBITDA | Δ vs committed | NPV @12% | IRR |
|---|---:|---:|---:|---:|
| A1 baseline | $0 | $0 | $0 | — |
| A2 disposal | $1.20M | +$6.00M | +$5.40M | — |
| B1 combust | $3.11M | +$6.00M | +$7.64M | 27.6% |
| C1 technical | $6.63M | +$5.83M | +$13.32M | 22.9% |
| C2 USP | $7.59M | +$5.83M | +$11.98M | 19.9% |
| E1 feed grade | $6.47M | +$6.00M | +$26.43M | 104% |
| E3 aggregation | $22.10M | +$17.50M | +$67.50M | 37.5% |
| F1 methanol only | −$0.08M | +$0.51M | −$3.71M | — |
| D1 propylene glycol | $1.06M | +$6.00M | −$22.53M | — |

Every route swings by about $6.0M/yr: the $4.0M charge no longer paid plus the
$2.0M cost avoided. That is larger than the entire EBITDA of any route in the
committed study, so the recommendation inverts and **minimum economic scale
ceases to exist** — there is no capacity at which NPV crosses zero from below.

### What survives, and what breaks

**Survives:** A1 still scores exactly $0.00. Its credit stream and the feed
transfer charge use the same price key and cancel regardless of sign, so the
baseline simply changes meaning from "collect $4M/yr" to "pay $2M/yr" and
remains the hurdle. The ranking machinery does not need redesigning.

**Breaks — two artifacts:**

1. **A2 double counts.** It is credited $2.0M for taking its own stream and pays
   only $0.8M (`solid_waste_disposal`) to dispose of it, netting a spurious
   +$1.20M EBITDA / +$5.40M NPV. Once the netback is negative, A1 and A2 are the
   same route described two incompatible ways.
2. **Correlated prices produce a fake winner.** `feed_grade_glycerin` ($525/t) is
   sourced directly from *Argus kosher crude 80% fob* — it is definitionally a
   crude glycerol assessment. Holding it at $525/t while the same commodity family
   goes to −$200/t implies a $725/t premium on a product whose base is worthless.
   Same issue, smaller, for the second-cut credit. And at −$200/t crude with
   $1,250/t technical, the implied spread is $1,450/t — wider than three of the
   four historical observations, when January 2024 shows refined *fell* with crude
   ($176/t crude against $772/t technical).

### Naive-override breakevens (crude netback for NPV = 0)

| Route | Breakeven netback |
|---|---:|
| B1 | −$33.9/t |
| C2 | $56.6/t |
| C1 | $94.3/t |
| E3 | $307.6/t |
| E1 | $385.7/t |

---

## 4. The architectural change

### 4.1 Split the overloaded price key

`crude_glycerol` currently does four jobs that coincide only while the price is
positive:

| Job | Location |
|---|---|
| A1 baseline netback (defines the hurdle) | `routes.py` A1 credit stream |
| Feed transfer charge in every route | `model.py:210` |
| Second-cut co-product price (C1/C2/E3) | `routes.py:277` |
| Third-party purchase price (E3) | `routes.py:334` |

Under a negative price these diverge in sign *and* meaning. Minimum split:

- `crude_disposal_cost` — positive, a cost, same convention as
  `solid_waste_disposal`
- `crude_glycerol_netback` — **derived as the negative of the above**, used only
  for the feed transfer charge
- `second_cut_glycerine` — an 87% salt-free cut is a different commodity from 80%
  crude and is probably a smaller liability, or positive
- `third_party_gate_fee` — best modelled as
  `crude_disposal_cost × capture_fraction`, because a competitor will only pay
  less than their own disposal alternative minus their freight

### 4.2 Re-establish the zero-hurdle invariant deliberately

Today "baseline EBITDA ≡ 0" holds *by accident*, because one key sits on both
sides of the equation. Once the keys are split, the tornado can move the netback
without moving the disposal cost, A1 stops being zero, and the comparator
silently loses meaning. Derive one from the other at module level and assert the
invariant in a test.

Then restate A1 as "dispose of crude glycerol", with the cost expressed as a
`purchased` line and the transfer credit on the other side. It still nets to
zero, but it reads correctly and avoids A1 reporting negative revenue in the
workbook. **Retire A2 as a route** — what it now represents is a sensitivity on
the disposal cost.

### 4.3 Make the spread the primary variable

The tornado and Monte Carlo draw every price independently. With crude negative
and refined fixed, the implied spread is historically implausible. The report
already argues rhetorically that "the spread IS the purification business" — so
sample the **spread** and derive the refined price from crude + spread, rather
than sampling both. The four-point history in `GLYCERINE_HISTORY` is enough to
parameterise it.

### 4.4 Add staged investment

Every route is a monolith with a single capex at t=0. **E1 is C1's front end** —
C1's pretreatment block already contains methanol recovery — so "build E1 now,
add the rest if needed" is a real option the model cannot express. The brief
explicitly invites it (§4, "modest purification now, conversion capacity added
later").

### 4.5 Add an avoided-cost ramp

The $2M/yr is a contract. If there is a term with a volume commitment, the
avoided cost cannot be booked on day one. The model's only time-varying hook is
`revenue_ramp`, which scales product revenue only (`model.py:380`). Deferring
$2M/yr of avoided cost through five operating years costs about **$4.8M of NPV**
at 12% after tax — survivable for E1, but roughly a third of C1 and E3.

### 4.6 Revisit the discount rate's justification

The 12% rate is justified partly on "the revenue line is exposed to a violently
cyclical commodity spread." That no longer applies uniformly: E1's value is
avoided contractual cost plus a local feed sale, while C1's is still the spread.
The cheap route is now also the *low-risk* route. Applying 12% throughout is
conservative, which is the right direction — but say so rather than letting it
pass silently.

### 4.7 Fix search brackets and the report's spine

- `run.py:171` product-price bracket `[200, 6000]` and `run.py:173` crude bracket
  `[0, 1200]` exclude the entire relevant region
- `run.py:182` capacity brentq `[10000, 200000]` will find no sign change and
  write an exception string into the workbook
- `figures.py:36` performs the same solve with **no exception handling** and will
  hard-crash
- §2.1, §2.2 and fig1 are all built on minimum economic scale. Reframe the
  capacity sweep from "what scale is required" to "what scale adds"

### 4.8 Re-litigate the Pass 1 gates

Several kills were "the market cannot absorb this volume", and that gate weakens
when the alternative is paying to destroy the material — revisit **D6 solketal**
and **D10 polyglycerols**. Conversely, B1's acrolein emissions and New York air
permitting were waved through as "passes all technical gates, killed on
economics"; if B1 becomes a finalist that question becomes load-bearing.

**B2 and B3 were never implemented.** The 22 routes are A1, A2, B1, C1–C3,
D1–D12, E1–E3, F1 — no steam reforming, no AD co-substrate. Under the old basis
that omission was defensible. Under the new one, **B3 is the disposal
alternative that sets the ceiling on the $200/t**, and with RIN or LCFS credits
it may not be a cost at all. It must be modelled, and the report should stop
saying "twenty-two candidates screened" without noting the two it dropped.

---

## 5. The barrier concept

The premise is that this client's crude has a −$200/t netback while the merchant
market is +$400/t. That is a contradiction unless something specific to *this
stream or this site* blocks access to the market. That obstruction is the
**barrier**. It is not a price — it is physical or commercial, and the model can
currently represent only its consequence (the negative netback), not the thing
itself.

It matters because each candidate barrier is removed by different equipment at
wildly different cost, so **identifying the barrier is the route selection**:

| Candidate barrier | Evidence in this stream | What removes it | Cost |
|---|---|---|---|
| Methanol at 9 wt% (90,000 ppm) | 18× the AAFCO 5,000 ppm limit; handling and flammability concern for buyers and haulers | Stripping column | ~$3.5M (E1/F1) |
| Ash, soaps, MONG | 1.5% ash + 1.5% soaps + 3% FAME; refiners discount or reject high-ash crude | Acidulation, phase split, vacuum distillation | ~$22M (C1) |
| No local buyer / freight economics | Upstate NY to Gulf or Midwest at $80–180/t against a $400/t product; inverts if the nearest refiner exits | Nothing in the purification set; only on-site consumption | ~$8.4M (B1) |
| Loading and storage infrastructure | No rail siding, truck loading or surge tankage | Tankage and loading | ~$0.5M |
| Contract lock-in with the hauler | They already pay $2M/yr | Legal, not capital | $0 |

The architecture implication: under client-specific stranding the netback is not
a scalar, it is a **function of which barriers a route removes**. A route should
declare the barrier set it clears, and the achieved netback should follow.

---

## 6. Scenario results (split keys)

Third-party crude and second-cut priced separately from the client's own netback,
as §4.1 proposes.

| Route | TCI | S1 — methanol barrier | S2 — ash/quality barrier |
|---|---:|---:|---:|
| A1 baseline | $0 | $0 | $0 |
| **E1** feed grade | $3.51M | **+$26.43M, IRR 104%, 0.7 yr** | −$4.19M, never |
| F1 methanol only | $3.51M | +$21.65M, IRR 90%, 0.8 yr | −$3.71M, never |
| C1 technical | $21.75M | +$14.06M, IRR 23.4%, 3.6 yr | **+$14.06M, IRR 23.4%** |
| C2 USP | $25.97M | +$12.75M, IRR 20.4%, 4.2 yr | +$12.75M, IRR 20.4% |
| E3 aggregation 30 kt | $42.04M | +$15.51M, IRR 18.8%, 4.3 yr | +$15.51M, IRR 18.8% |
| B1 combust | $8.35M | +$7.64M, IRR 27.6%, 3.0 yr | +$7.64M, IRR 27.6% |

Note E3 at +$15.5M rather than the naive +$67.5M — that $52M was almost entirely
the phantom gate fee, and splitting the key removes it.

**Two findings.**

1. **The mechanism is the recommendation.** If methanol is the barrier, E1 wins
   and a $22M refinery destroys $12M of value versus a $3.5M column. If ash is
   the barrier, E1 is worthless and C1 is required. Same client, same disposal
   cost, opposite answer.
2. **B1 is invariant.** Identical in every scenario, including a market-wide
   downside run for contrast, because it sells displaced natural gas and touches
   no glycerine price anywhere. 27.6% IRR and a 3-year payback on $8.4M
   regardless of which branch is true. It wins no scenario and loses none — the
   minimax choice while the mechanism is unresolved.

A market-wide contrast case (neighbours stranded too, refined falling to the
January 2024 level of $772/t technical) puts C1 at −$3.03M and C2 at −$6.82M,
i.e. purification fails again. E1/F1 were *not* internally adjusted in that run
(feed grade was left at $525/t), so their figures there should not be quoted.

---

## 7. E1 decomposed

The headline is arithmetically correct but is mostly a **price assumption**, not
a disposal finding.

### EBITDA build-up at −$200/t netback

| | |
|---|---:|
| Product: 9,145 t × $525/t | +$4.801M |
| Methanol credit: 855 t × $600/t | +$0.513M |
| Avoided disposal: 10,000 t × $200/t | +$2.000M |
| Utilities (gas $76k, elec $12k, CW $5k, WW $10k) | −$0.103M |
| Fixed opex (1.92 FTE = $202k labour, $128k maintenance, $228k overhead, $80k AAFCO/QC) | −$0.745M |
| **EBITDA** | **$6.465M** |

ISBL $1.83M · FCI $2.85M · TCI $3.51M · NPV $26.43M · IRR 104% · payback 0.71 yr

The product sale is **66%** of gross value; avoided disposal only **27%**.

### Three separable claims

| Claim | EBITDA | NPV |
|---|---:|---:|
| Tier 1 — avoided disposal + methanol only, product given away free | $1.66M | **+$4.82M** |
| Tier 2 — plus material sells at the *ordinary* crude price, $400/t | $5.32M | +$21.29M |
| Tier 3 — plus kosher/feed premium to $525/t (headline) | $6.47M | +$26.43M |

**$16.5M of the $26.4M rests on the single assumption that stripping methanol
moves the same material from −$200/t to +$400/t** — a $600/t discontinuity across
one column. Only $4.8M is anchored in an invoice already paid and a physical
recovery.

### Sensitivity to achieved price

| Achieved price | NPV | IRR |
|---:|---:|---:|
| $525/t | +$26.43M | 104% |
| $400/t | +$21.29M | 89% |
| $300/t | +$17.17M | 77% |
| $200/t | +$13.06M | 64% |
| $100/t | +$8.94M | 50% |
| $0/t | +$4.82M | 34% |
| −$100/t | +$0.67M | 16% |
| −$200/t | −$4.19M | — |

**Breakeven achieved price: −$115.5/t.**

### Why the IRR looks absurd, and what to quote instead

EBITDA is 1.8× TCI and payback is 0.71 yr, so IRR above 100% is arithmetic, not
insight. The 2-year construction profile actually *depresses* it — a single
stripping column is realistically a 9–12 month build. IRR here is dominated by
the timing of the first cash flow and says nothing about whether the price is
right. **Do not lead with it.**

Lead with the breakeven: the de-methanolised material need only be worth more
than −$115/t. If stripping methanol merely takes disposal from $200/t to below
$115/t, the column clears a 12% hurdle **on avoided cost alone, with no feed
market required.** That makes E1 the most *robust* route rather than the most
profitable one, and robustness is the better claim because it survives the
branch that cannot yet be resolved.

---

## 8. Design error found in the committed code

`METHANOL_RECOVERY = 0.95` leaves 45 t/yr of methanol in 9,145 t of product =
**4,920 ppm**. Against the AAFCO 5,000 ppm limit that passes by 1.6% — no margin
on the binding spec — and it is roughly **5× over** the 1,000 ppm Canadian
beef-cattle limit that the E1 description in `routes.py` claims the column meets.
Reaching 1,000 ppm requires about **99% recovery**.

So tier 3 revenue is not available from the design that is priced. The fix is
cheap — a taller column and more reflux, against a current gas bill of only
$76k/yr, so under ~$0.5M of extra TCI against a $26M NPV — but **the design basis
and the description string both need correcting.**

Separately: stripping methanol leaves the 1.5% ash, 1.5% soaps, 3% FAME and 5%
water untouched. Feed grade requires the whole spec to pass — sodium load and
MONG matter in ruminant diets — so tier 3 is contingent on more than methanol.

This is the one item that is a genuine bug in committed code rather than a
consequence of the new basis, so it is worth fixing on `main` regardless of where
this branch lands.

---

## 9. Open questions and next actions

### The revealed-preference problem

They pay $2M/yr today. If a $525/t feed market existed locally they would be
leaving roughly $7M/yr of gross swing on the table, and a consultant cannot
assume a client is irrational. So their behaviour is *evidence about the
mechanism*, and it is free. Note also that the cheaper the fix, the harder it is
to explain the inaction — **inaction is weak Bayesian evidence for the expensive
barrier**, which argues against anchoring on S1 just because its numbers are
spectacular.

### Sequenced actions

1. **Name the stranding mechanism.** Two assays (methanol and ash against the
   feed and refiner specs) plus one question to the hauler about where the
   material actually goes. ~$25k, resolves a $12M spread between
   recommendations.
2. **Get the hauling contract** — term, escalator, volume commitment,
   termination. It sets both the baseline and the timing of every avoided-cost
   credit, and its renewal date is probably the most decision-relevant number in
   the engagement.
3. **Price the AD alternative (B3).** It caps the $200/t and may be cheaper than
   anything built.
4. **Upgrade the $2M/yr to `sourced`** in the assumption register, citing the
   client invoice. It is higher quality than any Argus assessment and should be
   presented as a strength of the revised basis.

### Decision structure

- Methanol is the barrier → **E1**, $3.5M, best in class
- Ash/quality is the barrier → **C1** ($21.8M) or **E3** ($42.0M)
- Mechanism unresolved → **B1**, $8.4M, 27.6% IRR regardless
- The −$115/t breakeven means E1 can be committed *before* the diligence returns

Staging dominates in principle: E1 is C1's front end, so building E1 first is a
first stage rather than a sunk cost. Back-of-envelope, staging pays if there is
more than about a one-in-three chance methanol is the binding barrier; below
that, build C1 outright. This is not modelled — see §4.4.

### Framing for the report

This is a **basis change, not a correction** like those in §2.3. Both answers are
correct under their own basis, and the committed price history has crude at
28.5 ¢/lb in 2022 and 8 ¢/lb in 2024. Keep the positive-netback case as a
documented scenario rather than overwriting it; the recommendation becomes
conditional on which regime the client is in, and that conditionality is the
honest deliverable.

Worth noting: the basis flipped, the recommendation flipped, and the
highest-value next action did not — the committed report's "$25k, not $3.5M"
survives intact. That is a good sign about the analysis rather than a
coincidence.
