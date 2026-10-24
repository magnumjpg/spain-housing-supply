# RED_TEAM.md — attacking the project before someone else does

Written as if I were a referee hostile to the result. Each objection, then what
the project does about it, then what remains unresolved.

---

## "Your null is just a bad measure."

**Fair.** `share_nonurbanizable` is a share of municipal area and correlates with
rurality. The project says so and shows the raw-vs-adjusted figure precisely to
demonstrate the artefact.

**But** the critique cuts both ways: the same coarseness would bias *towards*
finding an effect if any existed in the direction of the hypothesis, because
restricted municipalities are systematically expensive coastal/urban ones. The
observed sign is the opposite, so measurement error alone does not explain it
away. The honest conclusion is "not identified", not "no effect".

**Unresolved:** a parcel-level or capacity-weighted measure would be better. Not
available in a reproducible public form.

---

## "You added controls until the result disappeared."

**Partially fair, and worth confronting directly.**

The controls were specified by the confound, not by the result: density and
consolidated-urban share are the obvious determinants of both land
classification and rents. They were chosen before the adjusted run, and the basic
vs urban pair is shown side by side in figure 3 rather than only the version that
supports the story.

**However:** the choice to *report* the urban-control version as the headline is
a judgement. A reader who prefers the basic specification sees −0.10, p < 0.001,
still the wrong sign. So the conclusion is robust to that choice, which is the
real defence.

---

## "With 431 municipalities and 52 clusters you cannot distinguish 0 from −0.05."

**Correct.** The confidence interval on non-urbanizable share is roughly
[−0.12, +0.03]. The project does not claim the coefficient is zero. It claims the
predicted negative effect is not detectable, and the point estimate is small and
of the wrong sign.

The two coefficients that are significant (pending share, unstarted share) are
reported but not treated as discoveries: they are 2 of 20 specifications and
would not survive a Bonferroni correction.

---

## "The pipeline gap could just be the 2008 crash."

**Plausible and not excluded.** Much of the planned stock was drawn up before
2007; the crash stopped construction; the SIU snapshot in the 2020s still counts
it as pending.

**What the project can say:** the gap is not cleared by demand. Fast-growing
municipalities still have 71% pending. That weakens, but does not eliminate, the
"it is all legacy 2007 stock" explanation — a fast-growing municipality could
still be sitting on 2007 paper.

**What would settle it:** plan dates per sector, which the SIU does not provide
in a comparable form.

---

## "You are implying hoarding without evidence."

The README explicitly separates "not built" from "retained strategically". The
word "hoarding" does not appear as a finding. The interpretation section lists
financing, infrastructure, land assembly and phasing as candidate mechanisms and
says the data cannot distinguish them.

**Residual risk:** a reader skimming the charts may still infer speculation. The
figure titles are descriptive ("Where the paper housing is concentrated"), not
accusatory.

---

## "Municipal average rent is the wrong outcome."

**Correct, and stated.** The hypothesis is about the marginal new unit; the data
measure the average of the stock. This attenuates any true effect towards zero.
It is one of the reasons the null is not strong evidence against the hypothesis.

---

## "You dropped the 2025 observations to make the sample look complete."

The panel keeps 2025. Rent regressions drop those rows because rent is missing,
not by an explicit filter. `coverage.json` reports both the panel span and the
non-missing counts per variable. A reader can reconstruct exactly which rows each
model used via `n` in `results.json`.

---

## "The 5.17 million figure is a national total presented as if it were the universe."

It is not presented that way. Every mention is scoped to the 431 municipalities.
The SIU has 5,898 municipalities and its national aggregate would be larger;
the README calls the figure a lower bound on plan capacity in the sample.

---

## "Why no instrumental variable? Saiz (2010) did it with terrain."

Because a credible instrument needs terrain data at municipal level, and Spanish
municipal boundaries make the Saiz approach harder: many municipalities are
enormous and include both mountains and plains, so a municipal terrain index has
little within-unit meaning. Assembling it was out of scope for this iteration.

**If I had another week:** Copernicus DEM + municipal boundaries, compute the
share of land above a slope threshold, use it as an instrument for development
capacity, and be explicit that the exclusion restriction (terrain affects rents
only through land supply) is strong and probably violated by amenities.

---

## "The panel interaction is fragile."

**Yes.** Non-urbanizable × growth is −0.10 with year FE and −0.17 with
province-year FE; planned capacity × growth is −0.10 with year FE but −0.03
(p = 0.24) with province-year FE. The result depends on how regional shocks are
absorbed, which is a warning sign, and the README says so.

The panel is included because it is the best available check on the
cross-section, not because it identifies a supply elasticity.

---

## "This is a null result dressed up as a project."

**The strongest objection, and the one the project tries hardest to answer.**

The defence: the project has a large, directly measured, non-obvious descriptive
finding (3.49 million unbuilt planned dwellings, 48.8% of development land not
started, and a gap that demand growth does not close) *plus* a well-documented
failed identification attempt. The failed attempt is informative because the
naive result is so strong and so misleading, and showing why is useful to anyone
who works with municipal land data.

If a reader wants a positive causal headline, this is not the project. That is a
feature.
