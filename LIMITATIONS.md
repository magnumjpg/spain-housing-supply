# LIMITATIONS.md

The list is ordered by how much damage each item does to the conclusions.

---

## 1. The design cannot identify a causal effect of land classification

Land classification is chosen by the municipality. It responds to expected
demand, geography, landowner structure, local politics and the 2008 crash. The
cross-section therefore estimates a equilibrium relationship, not a treatment
effect.

The panel with municipality FE removes time-invariant municipal traits, but the
land measure is a snapshot, so only its interaction with population growth is
identified. A municipality that reclassifies land *because* rents are rising is
indistinguishable from one whose rents rise *because* it reclassified.

**Consequence:** every coefficient in this project is an association. The README
uses "associated with", never "causes".

---

## 2. The treatment is measured after part of the outcome

The SIU workbook used here is dated 2026 (image years mostly 2020–2025). Rents
run to 2024, and the panel starts in 2013. The land classification observed is
therefore partly the *result* of the housing market being measured.

This is a genuine problem, not a stylistic caveat. It would bias the
cross-section towards finding that places with more development land have higher
rents — which is exactly the positive sign observed. That is one reason the
positive coefficients are not interpreted as evidence against the restriction
hypothesis.

A historical SIU series or a reconstructed panel of plan changes would fix this.
Neither is available in the current release.

---

## 3. The land measure is coarse

`share_nonurbanizable` is a share of **total municipal area**, not of buildable
or serviceable land. A municipality can be 95% non-urbanizable and still have
abundant flat, serviced land next to its urban core. Another can be 60%
non-urbanizable with every remaining hectare on a slope.

`MunTotSue` includes mountains, rivers, military land and protected natural
parks. The measure conflates "protected" with "unbuildable" with "far away".

The project mitigates this with density and consolidated-urban controls, but does
not solve it.

---

## 4. The outcome is municipal average rent, not the rent of new housing

The hypothesis is about the price effect of releasing land. The data measure the
average rent of the existing stock in a municipality. New-build units are a small
share of that stock, and the rent series is smoothed.

So even a real effect on new-build rents would be diluted towards zero. **The
null result is partly a measurement-resolution result.**

### 4b. The SERPAVI check narrows this concern but does not remove it

Section 2b of the README repeats the cross-section with SERPAVI, a tax-based rent
series that is independent of INE 69330. It reproduces the null: the same two
coefficients are negative and the restriction measures stay insignificant. That
makes it harder to argue that the result is an artefact of one statistical
operation.

It does not fix the resolution problem. SERPAVI is also an average/median of the
existing rental stock, not the rent of new-build units, and it is narrower still:
collective residential buildings, tax declarations, censored small cells, and no
Navarra or Basque Country. Two smoothed stock measures agreeing is evidence about
the stock margin, not about the new-build margin where the hypothesis lives.

---

## 5. `munnvivpnd` is a stock, not a delay

`pending_dwellings` counts dwellings planned in development areas that had not
been materialised when the SIU image was taken. It does not carry a plan date, so
it cannot distinguish:

- planned in 2006, stalled since the crash;
- planned in 2023, not yet due;
- planned, sold, and deliberately phased over 15 years.

The README is explicit about this. The project does **not** claim that the
pending stock is evidence of land hoarding, speculation or obstruction. Those are
hypotheses the data cannot test.

The plan-vintage result (§5 of the README) reinforces the caution: median
pending share falls from 85% for plans under five years old to 58% for plans
over 30 years old. Part of the gap is simply capacity that has not had time to be
built. 74% of the pending dwellings nevertheless sit under plans approved more
than 15 years ago.

---

## 6. The sample is urban and not representative of Spain

431 municipalities, all of them in the INE Urban Indicators universe (roughly,
municipalities above 10,000 inhabitants plus provincial capitals). They hold 15.5
million dwellings, so they cover most of the housing stock, but they are not a
random sample of municipalities.

Rural municipalities, which are the majority by count, are absent. Since the
non-urbanizable share is highest in rural areas, this truncates the very
variation the hypothesis is about.

---

## 7. No income, so no affordability

Rent per square metre is not affordability. A municipality can have high rents
and high incomes. The project cannot compute rent-to-income at municipal level
with these sources, so it does not claim to.

I tried to add municipal income as a control from INE's *Atlas de Distribución
de Renta de los Hogares* (ADRH, table 30824). That table is published at census
tract / district / municipality level in one very large semicolon-separated CSV.
The download obtained here stopped mid-record at 219 MB, so the file could not be
validated or parsed reliably and **no income control is used**. The omission is
recorded rather than papered over: a municipal income control would absorb part
of the urban–rural gradient, which is exactly the variation the non-urbanizable
coefficient is picking up.

---

## 8. SIU coverage is not random

5,898 of ~8,131 municipalities report land classes. Non-reporting is correlated
with not having a general plan and with being small. The SIU aggregate (5.17
million planned dwellings) is therefore a **lower bound** on plan capacity in
Spain, not a national total.

The 5.17 million figure is also specific to development areas
(`areas_desarrollo_mun`). It excludes capacity that exists inside consolidated
urban land through infill and height increases, which is where much of the real
supply response happens in large cities.

---

## 9. Cross-sectional standard errors with 52 clusters

Clustering by province is the right level for planning regimes, but 52 clusters
is on the low side. The p-values should be read as approximate. The two
significant coefficients (pending share, unstarted share) would not survive a
severe multiple-testing correction across the 20 cross-section specifications,
and are not presented as discoveries.

---

## 10. What would actually move the project forward

In order of value:

1. **A historical SIU or a plan-change panel.** Would allow an event study and
   fix the timing problem in item 2.
2. **Cadastral vacant-lot data.** Would separate "not built" from "no demand" at
   parcel level.
3. **Municipal income (ADRH) with a proper crosswalk.** Would turn rent levels
   into affordability.
4. **Building permits at municipal level.** Would replace the SIU stock with a
   flow and give the pipeline a time dimension.

None of these is a robustness check. They are different data.
