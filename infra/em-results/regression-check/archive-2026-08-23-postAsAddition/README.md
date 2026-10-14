# Archived: regression check of the C1–C5 build with POST admitted ALONGSIDE PUT/PATCH

Run 2026-08-23 19:39–21:35 against jar `adcd09cb…`. **21 rows, 3 mismatches, 0 verdict changes.**

All three mismatches are Tier-1 *reset* arms, all the same effect: admitting POST as a guarded source
alongside PUT/PATCH makes `POST /reports` a second guard endpoint, so the phase builds a **second**
valid triple (`201/200/403` on the fixed target, `201/200/201` on the vulnerable one). Every 970
verdict was identical to the recorded one; the only thing that moved was the number of triples, and
only where a reset endpoint restores the state that would otherwise block the second attempt.

Kept as the measurement behind the decision to make POST a **fallback** instead (used only when
PUT/PATCH yield no guarded candidate), which restores exact reproducibility on Tier-1/Tier-2 while
still serving the POST-only surface (pyLoad declares zero PUT/PATCH in either spec).

Not a defect, and not a false positive: on the fixed target the extra triples were *additional*
opportunities to cry wolf, and none was taken.
