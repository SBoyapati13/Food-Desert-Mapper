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
