# DECISIONS.md — the choices, including the ones that cost me the original story

Chronological. Each entry says what was decided, what the alternative was, and
why.

---

## D1. Build on SIU + INE + Padrón, not on Idealista or a scraped portal

**Chosen:** official MIVAU land data + INE rent and population.
**Alternative:** Idealista/Fotocasa listing data, which is richer and more
granular.
**Why:** licensing, reproducibility and the ability to publish the pipeline. A
scraper that breaks in six months is not a portfolio asset. The cost is that
rents are annual municipal averages rather than listing-level, which is a real
limitation and is stated as such.

---

## D2. The unit of analysis is the municipality, not the parcel or the sector

**Alternative:** `tabla_sectores.xlsx` has 68,207 sectors with land class, use,
surface and buildability.
**Why not:** sectors do not map to rents. There is no rent outcome at sector
level. The municipal level is the finest geography where land classification and
a price outcome coexist.
**Cost:** all the aggregation problems in LIMITATIONS.md §3 and §4.

---

## D3. The hypothesis was stated before looking, and then reported as failed

The original framing was *"more classified development land → lower rents"*. That
was written down in the project charter before estimation.

The first run produced:

- raw correlation non-urbanizable share vs log rent: **−0.55** (wrong sign for
  the restriction story, and suspiciously large);
- development share vs log rent: **+0.30** (also wrong sign).

**Decision:** do not go looking for a specification that rescues the sign. Add
the controls that the confound obviously requires (density, consolidated urban
share, province FE) and report what happens. What happened is that the
coefficients collapsed to −0.05 and +0.01, insignificant.

**This is the most important decision in the project.** The alternative — trying
log specifications, dropping outliers, adding controls until the sign flipped —
would have produced a publishable-looking result and a dishonest one.

---

## D4. The headline moved from rents to the pipeline gap

Once the rent hypothesis failed, there were two options: bury the null in a
robustness table, or make the project about what the data actually show.

**Chosen:** make the project about the gap between planned and materialised
housing, and report the rent null prominently as a finding about identification.

**Why:** the gap is large (3.49 million dwellings, 67.5% of planned capacity),
measured directly, and not explained by demand growth. It is a real result. The
rent null is also a real result, and more useful to a reader than a fake positive.

---

## D5. No Monte Carlo, no synthetic counterfactual, no welfare triangle

The previous zoning project (audited separately) used a synthetic data-generating
process and a welfare calculation. Both were removed here.

**Why:** a synthetic DGP can produce any result the author wants, and a welfare
triangle requires an elasticity this design cannot estimate. Including either
would make the project look more sophisticated and be less true.

---

## D6. Province FE, not municipality FE, in the cross-section

Municipality FE would absorb the land measure entirely, since it is
time-invariant. Province FE is the finest fixed effect that leaves variation.

**Cost:** unobserved within-province heterogeneity (coastal vs inland, tourism vs
industry) remains. Coastal and size robustness checks are reported in
`outputs/tables/robustness.csv`.

---

## D7. Cluster standard errors by province

**Alternative:** robust SEs, or clustering by municipality (impossible in a
cross-section).
**Why province:** planning law and housing markets are regional. 52 clusters is
low but defensible; the limitation is stated.

---

## D8. Standardise measures to z-scores for the coefficient plot

The five measures have incomparable units (share of area, dwellings per 1,000).
Plotting raw coefficients on one axis would be meaningless. z-scores make "one
standard deviation" the common unit; the underlying per-percentage-point
coefficient is also stored in `results.json` for share measures.

---

## D9. Keep 2024 as the cross-section year even though 2025 is present

2025 rents are empty (year not closed). 2024 has 408 of 434 rent values and is
the latest complete year.

---

## D10. Drop 2025 from the panel's usable range but keep the rows

The panel runs 2010–2025 because population is available for 2025 and some
outcomes are too. The rent regressions naturally drop 2025 rows due to missing
rent. Filtering the panel would hide the coverage asymmetry; keeping it and
letting the estimators drop rows is more transparent. `coverage.json` reports
both the panel span and the non-missing counts.

---

## D11. Do not publish a national total of planned dwellings

It is tempting to say "Spain has 5.17 million planned dwellings". That number is
the sum over the 431 urban municipalities in the matched sample, not Spain. The
README says "in these 431 municipalities" every time. A national figure would
require the full 5,898-municipality SIU with a stock denominator, which is a
different calculation.

---

## D12. Manual code mappings are allowed, silent drops are not

Two municipality names did not match the Padrón token key. They were mapped by
hand and the mapping is in `config.py` with a comment. If any name fails to map,
`build_panel.py` raises. The alternative — `how="left"` and a silent NaN — is how
municipal datasets lose 20% of their rows without anyone noticing.

---

## D13. Report the plan-vintage result, which weakens the headline

After the pipeline finding was written up, a check on plan age showed that newer
plans have a much higher pending share (r = −0.36; 85% pending for plans ≤5 years
old, 58% for plans >30 years). This is a competing explanation for the gap and it
partially undermines the "paper housing is a problem" framing.

**Chosen:** put it in the README as section 5, add a figure, and state the
counter-fact (74% of pending dwellings sit under plans older than 15 years). Do
not bury it in a robustness table.

**Alternative rejected:** controlling for plan age in the regressions and
reporting only the adjusted gap. That would turn an honest limitation into a
footnote, and the reader would not see that the simplest explanation for part of
the gap is time.

---

## D14. Use `requests`, not PowerShell `Invoke-WebRequest`, for MIVAU

MIVAU returns 403 to `Invoke-WebRequest` and to the default Python user agent.
`requests` with a browser-like `User-Agent` works. This is documented in
`config.py` because it will bite anyone reproducing the work.
