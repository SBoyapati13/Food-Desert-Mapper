# Changelog

Methodology is recorded here before the results that depend on it are computed. Data updates are not listed; they are in `data/runs.jsonl`.

## v1 method, registered 2026-10-19 (before any v1 results were computed)

The project changes from v0 (a Streamlit app that mapped OpenStreetMap stores around a chosen city; kept in `legacy/streamlit_v0/`) to a statewide tracker of **walking access to full-service food stores**, starting with New Jersey and built so other states can be added by configuration.

What was looked at before writing this: the column layouts of the source files listed below, the count of New Jersey block groups in the ACS file (6,599), and the number of New Jersey SNAP records by store type and by year of authorization and end date (for example, 2,101 New Jersey supermarket, super store and large grocery records over 2005–2025). No distances, access measures or maps had been computed.

**Sources (all official, all published for every state)**
- Stores: USDA Food and Nutrition Service, Historical SNAP Retailer Locator Data (store type, coordinates, authorization date, end date; 2005 onward).
- People: U.S. Census Bureau 2020 population-weighted centroids of block groups (CenPop2020); American Community Survey 2020–2024 5-year estimates for block groups: total population (B01003), households by vehicles available (B25044), median household income (B19013), ratio of income to poverty (C17002).
- Streets: U.S. Census Bureau TIGER/Line 2024 all-lines edges, by county.
- Boundaries for display: Census cartographic boundary files (block groups, county subdivisions), 2024.

**Definitions**
1. **Full-service food store**: a SNAP-authorized retailer whose store type is Supermarket, Super Store or Large Grocery Store (the same three categories USDA uses for its large-retailer access measures). Other SNAP store types (convenience, small and medium grocery, combination, specialty, farmers' markets) are counted and reported but do not count as full-service access.
2. **Active on a date**: authorization date on or before the date, and end date blank or after it.
3. **Store site**: records within 50 metres of each other are one site, so an ownership change at the same location is not counted as a closure and an opening.
4. **Walking network**: TIGER edges with these feature classes, treated as two-way: S1200 secondary roads, S1400 local streets, S1640 service drives, S1710 walkways, S1720 stairways, S1730 alleys, S1740 private roads, S1780 parking-lot roads, S1820 bike paths, S1830 bridle paths. Excluded: S1100 limited-access highways, S1630 ramps, and all non-road features.
5. **Walking distance** for a block group: the shortest network distance from its population-weighted centroid to the nearest active full-service site, plus the straight-line distances from the centroid and from the store to their nearest network points.
6. **Low walking access**: walking distance over 1 mile (1,609 m), the USDA urban distance. Also reported at 0.5 mile.
7. **Households without a vehicle**: B25044 owner-occupied plus renter-occupied households with no vehicle available.
8. **Lower-income block group**: median household income at or below 80% of the state's median household income, or at least 20% of people below the poverty line. (USDA uses tracts; block-group estimates have larger margins of error, which are reported.)

**Headline measures**
- Households without a vehicle in block groups beyond 1 mile, statewide and in lower-income block groups.
- People in block groups beyond 1 mile.
- Full-service store sites active at the end of each year, 2015–2025, and block groups whose walking distance crossed 1 mile in either direction between the end of 2015 and the latest year.
- A town summary (county subdivisions): share of households without a vehicle beyond 1 mile.

**Wording.** "Low walking access", never "food desert" as a finding about a place: the measure covers one store type, by foot, from a block group's centre of population.

**Known limitations at registration**
- Stores across a state line are not counted in v1; block groups within 1 mile of the state border are flagged.
- SNAP authorization is a proxy for being open; a store that never accepted SNAP is missing.
- A block group's centre of population stands in for every household in it.
- TIGER streets omit many footpaths and do not mark sidewalks.

**Health checks (each run)**: source freshness, share of block groups whose centroid snaps to the network more than 500 m away, network size, and the number of full-service sites, each with stated thresholds in the code.

### v1 implementation details, registered 2026-10-19 (after looking at the source files, before any distances were computed)

The registration above left these open. They were settled after reading the SNAP, ACS, CenPop and TIGER file layouts and the record counts below, and before any network was built.

1. **Dates.** The SNAP file runs to 31 December 2025, so the year-end dates are 31 December 2015 through 31 December 2025.
2. **Records without a location.** Full-service records with latitude or longitude of 0 or blank (8 of 2,101 in New Jersey) are dropped and counted in the health report.
3. **One street network for every year.** The 2024 TIGER network is used for all eleven year-ends, so changes in distance come only from stores opening and closing, not from changes in the street file.
4. **Edges.** County files are combined and de-duplicated by TIGER line ID (TLID); edges meet where they share a TIGER node ID (TNIDF/TNIDT). Lengths are great-circle (haversine) distances between shape points.
5. **Network points.** Each edge is split so no piece is longer than 25 m, and a centroid or store is snapped to the nearest of those points (so the straight-line snap distance is overstated by at most 12.5 m). Snapping uses only parts of the network with at least 200 points (about 5 km of streets), so a centroid is not attached to an isolated driveway or path that leads nowhere.
6. **Unreachable.** A block group with no path to any full-service site is counted as beyond 1 mile and listed in the health report.
7. **Income.** The state median household income is the ACS state-level B19013 estimate. Where a block group's median income is not published, the poverty test alone decides; where neither is published, the block group is reported as unclassified, not as lower-income.
8. **People and households.** Headline counts use ACS 2020–2024 population (B01003) and no-vehicle households (B25044), held at those values for every year-end, so changes over time come only from store changes.
9. **Towns.** A block group belongs to the county subdivision that contains its population-weighted centroid.
10. **Border flag.** The border is the part of the state's TIGER/Line 2024 boundary (unclipped, so rivers and bays are included) that it shares with another state; coastline is not border. A block group is flagged when its centroid is within 1 mile in a straight line of that border.

## v1.1, registered 2026-10-19 — corrections made after the first v1 results were seen

An independent review of the first v1 run (re-built walking distances for 126 block groups, recomputed every headline number) confirmed the distances and the published figures, and found the problems below. Each change is listed with what it does to the published numbers, which were known when these changes were made.

1. **Metres per degree.** The 50 m site rule, network snapping and the border flag converted latitude with 110,574 m per degree (the equatorial value) instead of about 111,030 at New Jersey's latitude, so north–south distances were about 0.4% short. Fix: the 50 m rule is applied to great-circle distances; projections use the length of a degree at the state's latitude, and the border distance is recomputed at each block group's own latitude. Known effect: one more site (a BJ's 50.2 m from a Kmart record in Vineland stops being merged), and two block groups at the 1-mile border line swap flags.
2. **Towns across a county line.** The generalized boundary file put three block-group centroids in a town in a neighbouring county. Fix: a block group is assigned only to a town in its own county; if its centroid falls in no town of its county, it goes to the town of its county that overlaps its area most.
3. **Rounding.** Published walking distances were rounded to whole metres, so the half-mile figures could not be rebuilt from the CSV. Fix: distances are rounded to 0.1 m before any measure is computed, and those same values are published.
4. **Health checks brought into line with the registration.** Added the registered network-size check (total walkable length within 5% of the previous run) and freshness for the ACS and TIGER vintages (no more than 3 years behind the current year); unreachable block groups are now listed by ID; a new check counts block groups whose walking distance is shorter than the straight line to the nearest open site (must be 0). The largest-connected-part check (≥ 95%), added in v1 without registration, is registered here.
5. **Same-named towns on the site.** The town table and search keyed towns by name, mixing up, for example, the Hamilton townships in Atlantic and Mercer counties. Fix: towns are keyed by Census ID and shown with their county. Display only; no numbers change.
6. **Reporting.** The README states how many full-service sites are warehouse clubs only, that SNAP end dates can lag real closures, the network-to-straight-line ratio at walking distances rather than over random statewide pairs, and no longer claims smaller margins of error for totals (none are computed).

**Effect of v1.1 on the published numbers (first v1.1 run).** Full-service sites 988 → 989 at the end of 2015 and 1,077 → 1,078 at the end of 2025 (the BJ's in Vineland is now its own site; two Clifton records 50 m apart, one closed before 2015, are now one site). 33 block groups' walking distances changed by more than 2 m because the nearest network point changed under the corrected projection; the largest change is 750 m in block group 340230014111, which has no households without a vehicle. Block groups moving beyond a mile, 2015 to 2025: 187 → 188 (car-free households unchanged at 8,697). Car-free households beyond a mile and not near the border: 90,553 → 90,589. Half-mile figures for 2025: 212,066 → 212,380 car-free households. The 1-mile headline figures (98,560 car-free households; 42,739 in lower-income block groups; 101,616 at the end of 2015) are unchanged. Three block groups changed town; two swapped border flags (the count stays 378).

## v2 method, registered 2026-10-19 (before any v2 results were computed)

Five extensions. Everything in v1.1 stays unless changed here. What was looked at before writing this: the field layout and row count of the NJ Food Desert Communities block-group layer (1,015 block groups, 50 communities, 2010-vintage block-group IDs: 89% match 2020 IDs), the Census 2020–2010 block-group relationship file's existence and size, the TIGER county file, the list of TIGER edge files for NY, PA and DE, and the column layout of the housing repo's `data/raw/obligation_final.csv`. No v2 distance, fragility, closure, siting or comparison result had been computed.

### 1. Neighbouring states
- **States.** New York (36), Pennsylvania (42) and Delaware (10) are added with the same definitions and thresholds as New Jersey (lower-income: ≤ 80% of the state's median household income or ≥ 20% poverty).
- **Across the border.** For each state, stores and streets in every county of another state whose TIGER/Line 2024 boundary is within 10 km of the state's boundary are added to the store set and the street network. Block groups and all measures remain the state's own. The border flag stays, but now marks block groups whose nearest store may be across the line rather than ones where such stores are missing. Whether a river can be walked across is whatever the TIGER network says (a bridge counts only if a walkable feature class crosses it).
- **Health.** The unchanged checks apply per state. The network-size check compares against the previous run of the same state *and the same v2 border rule*, so the first v2 run of each state has no comparison.

### 2. One-store neighbourhoods (N-1)
- **Next walk.** For each block group and year-end, the walking distance to the nearest open full-service site after removing the site that is its nearest. Computed exactly up to 2 miles; anything further is reported as "over 2 miles" (the published value is capped at 3,218.7 m).
- **One-store block group.** Walk ≤ 1 mile and next walk > 1 mile: one closure would put it beyond a mile.
- **Site criticality.** For each open site at a year-end, the no-vehicle households in the one-store block groups whose nearest site it is.
- **Headline.** No-vehicle households in one-store block groups at the latest year-end, statewide and in lower-income block groups.
- **Method.** One Dijkstra run per class of sites, where sites in the same class are more than 6,437.4 m apart in a straight line (twice the 2-mile cap). Excluding a whole class cannot change any next-walk value of 2 miles or less.

### 3. Closures
- **Closure.** A site open at one year-end and not open at the next, or open at the previous run's latest SNAP date and not at this run's.
- **Impact.** The closed site's criticality at the earlier date: the no-vehicle households for whom it was the only full-service site within a 1-mile walk. Also reported: the no-vehicle households in block groups whose nearest site it was. Openings are listed the same way, with the no-vehicle households brought within a mile.
- **Publication.** Every closure from the end of 2015 onward goes on the site and into an Atom feed (`docs/data/<STATE>/alerts.xml`), newest first. The project sends nothing to anyone.
- **Wording.** "SNAP authorization ended", not "closed", in each entry. The page explains that an ended authorization usually but not always means a closure and can lag it.

### 4. Where one more store would help most
- **Candidate.** Any point of the usable walking network in the state. It is a point on the street network, not a vetted site.
- **Coverage.** The no-vehicle households in block groups beyond 1 mile at the latest year-end that would be within 1 mile of the candidate. Distance is the block group's snap plus the network distance; the candidate's own snap is zero.
- **Greedy ten.** Pick the best candidate, treat the block groups it covers as served, and repeat until ten are chosen. A second list does the same counting only lower-income block groups.
- **Reporting.** Each point is reported with its town and the no-vehicle households it adds, not with a street address.

### 5. NJ comparisons (New Jersey only)
- **NJEDA Food Desert Communities.** Source: the NJDCA/NJEDA "New Jersey Food Deserts Block Group Details" layer (1,015 block groups, designated 9 February 2022).
  - **Crosswalk.** Its 2010 block groups are mapped to 2020 block groups with the Census 2020–2010 block-group relationship file. A 2020 block group is in a Food Desert Community when at least half of its land area lies in designated 2010 block groups.
  - **Measures.** The agreement between the two measures, at the end of 2021 (closest to the January 2022 store data NJEDA used) and at the latest year-end:
    - the share of no-vehicle households beyond 1 mile that live in designated block groups;
    - the share of designated block groups' no-vehicle households beyond 1 mile;
    - lower-income block groups beyond 1 mile with the most no-vehicle households that are not designated, totalled by town;
    - designated block groups whose walk is under half a mile.
  - **Wording.** The two answer different questions: NJEDA scores supermarket access for all households, including by car, and combines 24 factors. Differences are reported as differences between the two measures, not as errors in the designation.
- **Fourth Round housing.** Source: `data/raw/obligation_final.csv` from github.com/SBoyapati13/nj-housing-pace (final prospective need by county subdivision), read at build time, with its commit recorded.
  - **Measures.** The share of statewide Fourth Round prospective need (affordable homes, 2025–2035) in towns where at least half of no-vehicle households are beyond a 1-mile walk at the latest year-end, and the 15 towns with the most prospective need in that group.
  - **Wording.** Town level only. Where the homes will be built within a town is not known, and an obligation is not a permit or a completed home.

### v2 amendment, 2026-10-19 (before any v2 result was computed)
- **Fourth Round source.** The registered file, `data/raw/obligation_final.csv`, turned out to hold only the 16 towns with a final or adopted number on file, not every town. It was replaced before any comparison was computed with the housing repo's statewide source, `data/raw/dca_final_summary.csv`: DCA's calculated prospective need for all 564 municipalities, the same numbers the housing project uses for its main figures.

### v2 corrections, 2026-10-19 (after the first v2 runs; before anything was published)
1. **Largest-network-part check.** With counties across the border included, a network can legitimately split into two large parts with no walkable crossing between them: Delaware's includes South Jersey across the Delaware River and Bay, and only 83% of its points are in the largest part. The check (≥ 95%) now counts the state's populated block groups whose snapped point is in the largest part, instead of all network points. This was found when Delaware's first v2 run failed the check.
2. **Re-authorizations are not closures.** The first New Jersey closure list put "SAVE-A-LOT 60060, Atlantic City" at the top: its SNAP authorization ended in November 2025, and 2,725 households without a vehicle had it as their only store within a mile. But the next day "Save A Lot 30187" was authorized at the same street address, geocoded 133 m away, just beyond the 50 m site rule. Of 324 ended authorizations, 55 had a new authorization beginning within 300 m in the same year. Rule: when an ended site has a site that began within 300 m (straight line) in the same period, both are reported as a replacement, with the other's name, and not counted as a closure or an opening. Walking distances are unaffected: they already reflect whichever site was open at each year-end.
3. **Snap and unreachable checks count households without a vehicle.** Pennsylvania's first v2 run failed two checks that were set on New Jersey. 1.33% of its populated block groups have a centre more than 500 m from a walkable line (limit 1%): 134 large rural block groups with 2,801 households without a vehicle, 0.6% of the state's. One block group (420893003132, a private community in Monroe County with no households without a vehicle) snaps into a part of the network with no store. Neither affects the measures, which are about households without a vehicle. The snap check now limits the share of *no-vehicle households* in block groups snapping more than 500 m away (≤ 1%). The unreachable check requires zero *no-vehicle households* in unreachable block groups. Both still report the block-group counts, and unreachable block groups are still listed by ID.
4. **ACS match check.** New York's first v2 run failed the check that every block group matches the ACS. 39 block groups in Suffolk County that have a 2020 population-weighted centroid have no row in the 2020–2024 ACS, which publishes revised block groups there; every ACS block group did match a centroid. The check is meant to catch a failed join, so it now requires every *ACS* block group to have a centroid. Block groups with a centroid but no ACS row are listed in the health report. They carry no households in the measures, and their people are counted in the neighbouring revised block groups, located at those block groups' 2020 centroids.

## v2.1, 2026-10-19 — corrections from the independent review of v2 (after v2 results were seen; before publication)

The review reproduced the walking distances, next walks, one-store totals, criticality, the best-site picks, the Food Desert Community comparison, the Fourth Round figures and the cross-border county lists. It found the problems below. All changes were made knowing the v2 results.

1. **Two earlier corrections are withdrawn because they loosened gates.**
   - *Correction 3 (snap and unreachable checks counted on car-free households) is withdrawn.* It was made right after Pennsylvania failed, and it changed the unit to one that forgives exactly that failure. The v1.1 checks are restored: share of populated block groups snapping more than 500 m away ≤ 1%, and zero unreachable block groups. The car-free-household values are still reported next to them.
   - *Correction 4 (ACS match check) is withdrawn.* Its reason was wrong. The 39 Suffolk County, NY block groups (74,263 people in 2020, in 14 tracts) are not in the 2020–2024 ACS summary file at all, at block-group or tract level, while the county total includes them. So about 75,000 people are missing from New York's figures. The original check (every block group with a centroid matches an ACS row) is restored.
   - Pennsylvania and New York now fail checks on the published site, and the banner says which. The banner's wording no longer says the figures "may be out of date": it names the checks and links to the health report.
   - Correction 1 (largest-part check per state) stands. Delaware's network really is split, because the bridges across the Delaware River and Bay carry no walkable feature class.
2. **Feeds are complete.** They were cut to the 300 newest entries, against v2 §3 ("every closure from the end of 2015 onward"). They now carry every entry.
3. **Closures between SNAP files are implemented.** v2 §3 registered transitions at "the previous run's latest SNAP date" as well as at year-ends, but only year-ends were computed. Evaluation points are now every year-end, every earlier v2 run's SNAP date after the last year-end, and this run's SNAP date. With the current file, which ends 31 December 2025, nothing changes.
4. **Same address counts as a replacement.** Re-authorizations at the identical street address were geocoded up to 1.5 km apart (Lidl 1177, Eatontown; Foodtown, Lake Hiawatha). An ended site and a new one in the same period are now paired if they share a normalized street number, street name and ZIP, or are within 300 m. Address matches are tried first, and each new site can be paired only once.
5. **Lapses are shown.** Some sites whose authorization ended were authorized again later at the same site; in New Jersey, 37 such sites accounted for about a fifth of the households counted. Each ended entry now records when the site was authorized again, if it was. The headline counts ended authorizations that were not renewed by the latest date, and the totals including lapses are still reported.
6. **Implementation details not registered in v2, now recorded:**
   - Next walk is computed with one 2-mile-bounded Dijkstra per store site (`local_table`), not the registered one run per class of sites. The two are equivalent: both give the exact next walk up to the 2-mile cap, and the review's independent check agreed.
   - The check that the shortest-path walk and the nearest-two table agree within 2 miles (`nearest_two_matches_walk`) was added in v2 without registration.
   - Ended or new authorizations of out-of-state sites are listed only when the site is the nearest store for at least one of the state's block groups.
7. **Changes v2 made to New Jersey's v1.1 figures, now documented** (as corrected by the re-review):
   - The 1-mile figures are unchanged in every year.
   - Car-free households beyond half a mile went from 212,380 to 212,329.
   - 50 populated block groups got shorter walks, by up to 17.6 km: stores across the border, mostly in Sussex, Hunterdon and Warren counties.
   - 15 populated block groups got longer walks, by up to 25.3 m. Snap distances are unchanged for most of them, so the likely cause is a store's snap point or the network around it changing when neighbouring streets were added; this was not investigated further.
   - An unpopulated block group (340210025005) now snaps 867 m across the Delaware River into Pennsylvania (3.6 km longer).
   - Populated block groups that snap to a point outside the state are now listed in each summary.
8. **Wording.** The page description and the feed's link title said "closures"; they now say ended authorizations. The Fourth Round comparison now reports its baseline: the share of the state's households living in the same towns.

### v2.1 addendum, 2026-10-19 — after a re-review of the v2.1 corrections (results known)
1. **Pairing before filtering.** Replacements were paired after out-of-state sites that are nobody's nearest store were dropped. That left one Philadelphia ShopRite listed as ended while its same-address successor had been dropped. Pairing now happens first.
2. **The out-of-state filter follows the recorded rule.** The rule says "nearest store for at least one of the state's populated block groups". The code had tested for at least one car-free household, which dropped two sites that are nearest for a block group with no car-free households. The code now follows the rule.
3. **Overlapping re-authorizations.** An ended site that shares a street address with another site open at both dates is reported as a replacement ("same address, already open"). This is a re-authorization that began before the old one ended, so the same-period rule missed it. The re-review found 17 such New Jersey entries (223 car-free households), 18 in New York and 37 in Pennsylvania.
4. **Sites, not entries.** Ended-authorization totals now count distinct sites. A site whose authorization ended twice was being counted twice; the entry counts are still reported.
5. **On the site.** The page now states the same-address rule and shows the Fourth Round baseline (the towns' share of the state's households).

## v3 method, registered 2026-10-19 (before any model was fit and before any housing site was extracted)

Two additions. Everything in v2.1 stays.

What was looked at before writing this:
- **Stores.** The count of in-state store-years and ended authorizations by year in the v2.1 outputs: 54,960 store-years and 1,206 ended authorizations across the four states.
- **Housing.** The list of the 16 largest DCA Fourth Round obligations.
- **Parcels.** The existence of New Jersey's statewide parcel composite map service.

No feature was computed and no model was fit. No housing plan was opened for its site list.

### A. Forecast: risk of losing walkable access next year

1. **Unit.** An in-state full-service site open at year-end *y*, for *y* = 2015…2024.
2. **Event.** Its authorization ends by year-end *y*+1 (kind "ended" in `closures.csv`). A replacement, or a site that continues at the same address, is not an event. A lapse that is later renewed is an event, because access was lost at the time.
3. **Features at *y*:**
   - store type;
   - chain size: the number of open sites in the four states sharing the store's brand, where the brand is the name with digits, punctuation and legal suffixes removed, taken to the first two words;
   - years since the site's first authorization;
   - number of earlier lapses;
   - other open full-service sites within ½ mile and 1 mile in a straight line, counting sites across the border;
   - sites that began within 1 mile in the previous year;
   - the site's criticality;
   - around the site (block-group centroids within 1 mile in a straight line): people, car-free share of households, poverty rate (population-weighted), and the nearest block group's median income as a share of the state median;
   - state.
4. **Models.**
   - (a) **Baseline:** the training-period rate by store type × state.
   - (b) **Logistic regression:** L2 penalty, C = 1; numeric features standardized; missing values set to the training median, with an indicator.
   - (c) **LightGBM:** fixed in advance, with no tuning on the test years: 15 leaves, learning rate 0.05, 300 trees, minimum 50 rows per leaf, 0.8 row and column sampling. Its output is isotonic-calibrated.
5. **Splits.**
   - **Test:** transitions from *y* = 2021–2024 (to 2022–2025).
   - **Training:** baseline and logistic are fit on *y* = 2015–2020. LightGBM is fit on 2015–2018 and calibrated on 2019–2020.
   - **Unused years:** test years are used for nothing but evaluation.
6. **Metrics.**
   - **Primary:** Brier score.
   - **Also:** Brier skill against the baseline, log loss, AUC, and calibration by deciles of predicted risk.
   - **Neighbourhood check:** among test block group-years within a 1-mile walk at *y*, the share of those that were beyond a mile at *y*+1 that fell in the top 5% of predicted neighbourhood risk; and the expected against the observed number of car-free households losing walkable access.
7. **Choice.** The model with the lowest test Brier score is used, if it beats the baseline; otherwise the baseline is used, and that is reported.
8. **From store risk to neighbourhood risk.**
   - **Risk.** A block group's risk is the probability that every full-service site within a 1-mile walk of it at *y* has its authorization end by *y*+1. That is the product of those sites' probabilities, treating closures as independent; it is the exact limit of the registered Monte Carlo, so no simulation is run.
   - **Limits.** Openings are not modelled, so this is a risk of loss. Block groups already beyond a mile have no risk under this definition.
   - **Sites outside the four states.** They get the full-period baseline rate for their store type.
   - **Data needed.** This needs the table of sites within 2 miles of each block group. `build.py` now writes it to `out/<STATE>/site_bg_2mi.csv.gz`, and nothing else in the build changes.
9. **Live forecast.** The chosen model is refit on every transition (*y* = 2015–2024) and applied at the end of 2025, giving the risk of losing access during 2026.
10. **Publication.**
    - **What is published:** block-group risk, state totals, the evaluation and the model's coefficients or feature importances.
    - **What is not:** site-level probabilities are neither published nor committed.
    - **Wording:** "risk of losing walkable access to a full-service store", not a prediction about any business.

### B. Fourth Round housing sites (New Jersey; the 15 largest obligations)

1. **Towns.** The 15 municipalities with the largest DCA prospective need: Paramus, Secaucus, Wayne, Roxbury, South Brunswick, Jackson, Linden, Monroe (Middlesex), Wall, Edison, Franklin (Somerset), Old Bridge, Hardyston, Toms River, West Windsor.
2. **Source.** Each town's most recent available Fourth Round Housing Element and Fair Share Plan: adopted, draft, or the version filed with the court or the dispute program. The document URL and page are recorded for every site.
3. **Sites.** Every location the plan relies on for new affordable units toward its prospective need, whether inclusionary development, 100% affordable development, overlay or redevelopment zone, or a group home with a fixed address. Each has its block/lot or address and the affordable units (or credits) the plan assigns it. Excluded: credits with no location, bonus credits, extensions of expiring controls, and mechanisms without a site.
4. **Extraction.** Read from the documents by Claude (LLM-assisted). Every row is then checked against the document by an independent agent, and disagreements are resolved by re-reading the page. A town with no findable plan is reported as missing, not estimated.
5. **Location.** The centroid of the parcel or parcels from New Jersey's statewide parcel composite, matched by municipality, block and lot. If no block/lot is given, by address in the same layer. Unmatched sites are listed.
6. **Measures.** At the end of 2025, with v2.1's network, snapping and store rules:
   - each site's walking distance to the nearest open full-service site, its next walk, and whether it is in a one-store position;
   - for each town and overall: the share of affordable units beyond a 1-mile walk and within ½ mile, compared with the share of the town's existing car-free households beyond a mile.
7. **Wording.** A plan site is not a permit or a built home. The measure is walking access to full-service food stores only.
