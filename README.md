# Walking access to full-service food stores: New Jersey, New York, Pennsylvania, Delaware

**Live map:** https://sboyapati13.github.io/Food-Desert-Mapper/ (pick a state; `?s=NY`, `?s=PA`, `?s=DE`)

For every census block group in four states, the walking distance along streets and paths from where its people live to the nearest full-service food store, at the end of each year since 2015. It also tracks:
- which neighbourhoods depend on a **single store**;
- which stores' **SNAP authorizations ended**, and who that affected (with an Atom feed per state);
- **where one more store would help most**.

The focus is households without a car, for whom walking distance is the binding constraint. Everything is built from public data published for every state (USDA SNAP retailer records, Census ACS, Census TIGER streets), and stores just across a state line count.

## Findings (stores open at 31 December 2025)

| | Households without a car | Beyond a 1-mile walk | In one-store areas¹ | Full-service sites, 2015 → 2025 |
|---|---:|---:|---:|---:|
| New Jersey | 389,559 | **98,560 (25%)** | 60,594 (16%) | 989 → 1,078 |
| New York | 2,254,645 | **188,869 (8%)** | 124,606 (6%) | 2,684 → 2,815 |
| Pennsylvania | 549,478 | **207,720 (38%)** | 116,979 (21%) | 1,657 → 1,679 |
| Delaware | 24,967 | **11,937 (48%)** | 6,290 (25%) | 111 → 130 |

¹ Within a 1-mile walk of exactly one full-service store: one closure would put them beyond a mile.

**New Jersey in more detail**
- **One closure away.** 60,594 more car-free households are within a mile of only one store. 35,378 of them are in lower-income block groups.
  - The store the most people depend on is the new Save A Lot in Atlantic City: 2,876 car-free households have no other full-service store within a mile.
  - Next are Twin City Supermarket in Jersey City (2,530) and Fine Fair Supermarket in Newark (1,673).
- **Ended authorizations.** 235 full-service sites in New Jersey had their SNAP authorization end between 2015 and 2025 (240 entries; five sites ended twice). That count excludes 77 re-authorizations or changes of operator at the same address or within 300 m.
  - 36 of the 235 sites were authorized again later at the same site.
  - The other 203 were not renewed. When they ended, they were the only store within a mile for 12,816 car-free households (16,426 including the lapses).
  - The largest single loss was Millville's Save-A-Lot in 2021 (1,373 households).
  - Next were Gala Fresh Farms in Passaic in 2018 (818; a new authorization at the same site followed in 2024) and Incollingo's in Penns Grove in 2023 (641).
- **Where a new store would help most.** A single store in Camden would bring 2,044 car-free households within a mile, the most anywhere in the state. Millville (1,522), Bayonne (1,316), Trenton (1,250) and Atlantic City (1,130) follow. These are points on the street network, not vetted sites.
- **The state's Food Desert Communities measure something different.** New Jersey designated 50 Food Desert Communities in 2022.
  - At the end of 2021 (closest to the store data NJEDA used), only 16% of the state's car-free households beyond a 1-mile walk lived in them.
  - Only 11% of the car-free households inside them were beyond a mile; 77,079 of them were within half a mile.
  - The designation scores supermarket access for all households (including by car) and combines it with 24 other factors, so this is a difference between two measures, not an error in either.
  - At the end of 2021, 499 lower-income block groups beyond a mile were not designated (491 at the end of 2025). The towns with the most car-free households among them are Manchester and Berkeley townships (Ocean County), Vineland, and Monroe township (Middlesex).
- **Fourth Round housing.** 68% of the statewide Fourth Round affordable-housing obligation (54,769 of 80,798 homes, DCA calculation) falls in towns where at least half of car-free households are more than a 1-mile walk from a full-service store.
  - Those 348 towns hold 50% of the state's households, so the obligation leans toward them.
  - This is at the town level only: where the homes will go within each town is not known.

**Risk of losing access next year (forecast, v3).**
- **The model.** A logistic model of ten years of SNAP authorization endings (55,000 store-years in four states) gives each store a chance that its authorization ends next year. A block group's risk is the chance that every full-service store within its 1-mile walk has its authorization end.
- **Published by county only.** A block group with one store would reveal that store's probability, and the project does not publish predictions about individual businesses.
- **New Jersey, 2026:** about 1,600 car-free households are expected to lose walkable access (1,000 in lower-income block groups), and 125 block groups have a risk of 5% or more.
- **How good it is.** Endings are hard to predict.
  - **Ranking stores.** On 2022–25, held out, the model ranked stores better than closure rates by store type (AUC 0.66 vs 0.59), but it barely improved the Brier score (+0.3%) and over-predicted endings.
  - **Ranking neighbourhoods.** 32% of the block groups that actually lost access fell in its top 5% of risk, against 27% using store-type rates and 14% using one rate for every store.
  - **Totals.** Its totals were off by state. In New Jersey it expected 7,564 car-free households to lose access over 2022–25 and 5,161 did, so read New Jersey's 2026 figure as likely too high. Treat all figures as rough and relative.

**Where the Fourth Round homes are planned (v3).**
- **What was scored.** Sites named in the housing plans of 9 of the 15 towns with the largest obligations. Each was located by block and lot in the state parcel layer and checked against the plan by a second reader.
- **Result.** 77% of the 3,113 located planned affordable homes are more than a 1-mile walk from a full-service store.
  - **Like-for-like comparison.** Weighting each town's existing car-free households the same way as its planned homes gives 69%.
  - **Town by town.** In 6 of the 9 towns, the planned homes are further out than the town's car-free households.
  - **Unlocated homes.** 440 more homes could not be located, mostly Linden overlay zones without lot numbers. If all were within a mile, the share would be 67%.
- **Town by town.** Jackson (1,000 homes, 96% beyond a mile), South Brunswick (90%) and Wall (91%) drive it. West Windsor (25%), Old Bridge (11%) and Paramus (14%) planned closer to stores than where their car-free households live now.
- **Not yet covered.** Secaucus, Roxbury, Edison, Franklin and Toms River: their plans couldn't be read or found. Hardyston names no Fourth Round sites.

**Across the line.** 21 New Jersey block groups now have their nearest store in another state. TIGER does not map the walkways on the Ben Franklin or George Washington bridges, so Camden to Philadelphia and Fort Lee to Manhattan are not walkable in this network. The Delaware River bridges at Trenton, Lambertville and Phillipsburg are.

**Margins of error.** These are 5-year ACS estimates at the block-group level. Margins of error on household counts are large for individual block groups (they are shown on the map); no combined margins are computed for totals.

## Method (v2)

Every method version is registered in [CHANGELOG.md](CHANGELOG.md) before its results are computed. Corrections made after results were seen are listed separately with their reasons and effects: six in v1.1, four in v2, and eight in v2.1, plus a five-item addendum after a second review. Three of the v2 corrections changed health checks after a state failed them. v2.1 withdrew two of them after independent review, because they loosened the gate; it kept the third (the largest-network-part check per state), because Delaware's network really is split by the Delaware River and Bay.

| | |
|---|---|
| Full-service store | SNAP-authorized retailer of USDA store type Supermarket, Super Store or Large Grocery Store |
| Open on a date | authorization date on or before it, end date blank or after it |
| Store site | records within 50 m (great-circle) of each other are one site |
| Stores across the border | stores and streets in every county of another state within 10 km of the state's boundary |
| Walking network | TIGER/Line 2024 edges: secondary roads, local streets, service drives, walkways, stairs, alleys, private roads, parking-lot roads, bike and bridle paths; excludes limited-access highways and ramps; two-way; the same network every year |
| Where people are | 2020 population-weighted centre of each block group |
| Walking distance | shortest network path to the nearest open site, plus straight-line snaps to the network at both ends |
| Low walking access | over 1 mile (1,609 m); 0.5 mile also reported |
| One-store block group | walk ≤ 1 mile, and > 1 mile to the next-nearest open site |
| Site criticality | car-free households in the one-store block groups whose nearest site it is |
| Ended authorization | site open at one evaluation date (each year-end, and each SNAP file date after the last year-end) and not at the next. If a new site began in the same period at the same street address or within 300 m, both are reported as a replacement instead. Each entry records whether the site was authorized again later |
| Best new site | greedy choice of network points in the state, each bringing the most car-free households (in block groups beyond 1 mile) within a mile |
| Households without a vehicle | ACS 2020–2024 B25044, owner plus renter households with no vehicle |
| Lower-income block group | median household income ≤ 80% of the state median, or ≥ 20% of people below poverty (C17002) |
| Town | county subdivision of the block group's own county containing its centre of population (otherwise the one overlapping it most) |

**Wording.** "Low walking access", not "food desert". "SNAP authorization ended", not "closed".

**Known limits.**
- **Bridges and islands.** Bridge walkways missing from TIGER (above) make some river crossings and islands unwalkable. In New York, 11 island block groups (Governors, Randalls and Wards, Fire Island, the Thousand Islands, and others) with 28 car-free households have no walkable path to a store.
- **SNAP as the store source.** SNAP authorization stands in for being open: a store that never took SNAP is missing, and an end date can lag the real closing.
- **Store types.** Store-type classes are USDA's: some warehouse clubs count, and a few small grocers may be under-classed.
- **One point per block group.** One centroid stands in for every household in a block group.
- **Sidewalks.** TIGER does not map sidewalks.
- **Fixed population.** Population and households are held at 2020–2024 levels, so changes over time reflect store changes only.
- **Missing Suffolk block groups.** In New York, 39 Suffolk County block groups (74,263 people in 2020, in 14 tracts) are missing from the 2020–2024 ACS summary file at both block-group and tract level, though the county total includes them. About 75,000 people are therefore missing from New York's figures.

## Checks on every run

The site shows a banner naming any check that fails. The checks are:
- populated block groups whose snapped point is in the network's largest connected part (≥ 95%);
- share of populated block groups more than 500 m from the network (≤ 1%; the car-free households in them are also reported);
- block groups with no path to any store (0; listed by ID, with their car-free households);
- block group-years where the walk is shorter than the straight line to the nearest open site (0);
- agreement between the two distance computations (shortest-path tree and nearest-two table) within 2 miles (0 mismatches);
- change in total walkable length since the previous run (≤ 5%);
- full-service records without coordinates (≤ 2%);
- age of the SNAP file (≤ 550 days);
- ACS and TIGER vintages (no more than 3 years old);
- every block group with a 2020 centroid matched to an ACS row.

**Current status:**
- New Jersey and Delaware pass every check.
- Pennsylvania fails two:
  - 1.33% of populated block groups are more than 500 m from a walkable line. These are rural block groups with 0.5% of the state's car-free households.
  - One block group, a private Monroe County community with no car-free households, has no path to a store.
- New York fails three:
  - 1.61% of block groups are more than 500 m from the network;
  - the 11 island block groups have no walkable path;
  - the 39 Suffolk block groups have no ACS row.

**Every run is logged.** Each run is appended to `data/runs.jsonl` with source hashes. There have been two independent reviews. The first rebuilt the network and distances for 126 New Jersey block groups and matched within the 25 m tolerance. The second independently recomputed nearest and next-nearest walks for 66 New Jersey block groups (largest difference 31 m), and reproduced site criticality, the best-site picks, the Food Desert Community comparison, the Fourth Round figures and the cross-border county lists.

## Reproduce

```
pip install -r requirements.txt
python3 src/fetch.py NJ     # sources: ~1 GB cached in data/cache for all four states; state extracts in data/raw/<STATE>
python3 src/build.py NJ     # NJ ~5 min, PA ~20 min, NY ~16 min, DE ~1 min; 2–5 GB of memory
python3 src/forecast.py     # after every state is built: closure-risk models, evaluation, neighbourhood risk (~4 min)
python3 src/housing_sites.py   # NJ Fourth Round sites: parcel lookup and walking access (~3 min)
python3 src/web.py          # docs/ site for every built state
```

A scheduled GitHub Action (`.github/workflows/update.yml`) checks the sources monthly, rebuilds the states whose sources changed, regenerates the feeds and redeploys the site.

**Adding a state:** add it to `config/states.json` (FIPS code, name, and the two lower-income thresholds) and run the three commands with its postal code.

## Files (per state, in `out/<STATE>/`)

- `bg_access.csv`: one row per block group: walking distance (m) at each year-end (`walk_YYYY`), next-nearest (`next_YYYY`, capped at 2 miles), households, car-free households and margin, income, poverty, town, border distance, nearest site at the latest year-end; in New Jersey also the Food Desert Community flag.
- `sites.csv`: every full-service site (including across the border), the years it was open, and its criticality each year.
- `closures.csv`: every authorization that ended, began or was replaced, with its effect.
- `siting.csv`: the ten best new points, for all and for lower-income block groups.
- `towns.csv`, `years.csv`, `summary.json` (including the health report and the New Jersey comparisons).
- Feeds: `docs/data/<STATE>/alerts.xml`.

## Sources

- USDA Food and Nutrition Service, Historical SNAP Retailer Locator Data.
- U.S. Census Bureau:
  - American Community Survey 2020–2024 5-year estimates (B01003, B25044, B19013, C17002);
  - 2020 centers of population by block group;
  - TIGER/Line 2024 edges, counties and states;
  - 2024 cartographic boundary files;
  - 2020–2010 block-group relationship file.
- NJDCA/NJEDA, New Jersey Food Deserts Block Group Details (2022).
- NJ DCA Fourth Round calculations, as compiled in [nj-housing-pace](https://github.com/SBoyapati13/nj-housing-pace).
- Map tiles © OpenStreetMap contributors.

## Earlier version

v0 was a Streamlit app that mapped OpenStreetMap grocery stores around a chosen city. It is kept, unchanged, in [`legacy/streamlit_v0/`](legacy/streamlit_v0/).

Corrections and questions: [open an issue](https://github.com/SBoyapati13/Food-Desert-Mapper/issues).
