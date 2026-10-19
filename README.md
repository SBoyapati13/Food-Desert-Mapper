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
- **Ended authorizations.** 263 full-service sites in New Jersey had their SNAP authorization end between 2015 and 2025, not counting 55 re-authorizations or changes of operator at the same place. When they ended, those sites were the only store within a mile for 17,158 car-free households.
  - The largest single loss was Millville's Save-A-Lot in 2021 (1,373 households).
  - Next were Gala Fresh Farms in Passaic in 2018 (818; a new authorization at the same site followed in 2024) and Incollingo's in Penns Grove in 2023 (641).
- **Where a new store would help most.** A single store in Camden would bring 2,044 car-free households within a mile, the most anywhere in the state. Millville (1,522), Bayonne (1,316), Trenton (1,250) and Atlantic City (1,130) follow. These are points on the street network, not vetted sites.
- **The state's Food Desert Communities measure something different.** New Jersey designated 50 Food Desert Communities in 2022.
  - At the end of 2021, only 16% of the state's car-free households beyond a 1-mile walk lived in them.
  - Only 11% of the car-free households inside them were beyond a mile; 77,079 of them were within half a mile.
  - The designation scores supermarket access for all households (including by car) and combines it with 24 other factors, so this is a difference between two measures, not an error in either.
  - 491 lower-income block groups beyond a mile are not designated. The towns with the most car-free households among them are Manchester and Berkeley townships (Ocean County), Vineland, and Monroe township (Middlesex).
- **Fourth Round housing.** 68% of the statewide Fourth Round affordable-housing obligation (54,769 of 80,798 homes, DCA calculation) falls in towns where at least half of car-free households are more than a 1-mile walk from a full-service store. This is at the town level only: where the homes will go within each town is not known.

**Across the line.** 21 New Jersey block groups now have their nearest store in another state. TIGER does not map the walkways on the Ben Franklin or George Washington bridges, so Camden to Philadelphia and Fort Lee to Manhattan are not walkable in this network. The Delaware River bridges at Trenton, Lambertville and Phillipsburg are.

**Margins of error.** These are 5-year ACS estimates at the block-group level. Margins of error on household counts are large for individual block groups (they are shown on the map); no combined margins are computed for totals.

## Method (v2)

Every method version is registered in [CHANGELOG.md](CHANGELOG.md) before its results are computed. Corrections made after results were seen are listed separately with their reasons and effects: six in v1.1 and four in v2.

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
| Ended authorization | site open at one year-end and not the next. If a new site began within 300 m in the same year, it is reported as a replacement instead |
| Best new site | greedy choice of network points in the state, each bringing the most car-free households (in block groups beyond 1 mile) within a mile |
| Households without a vehicle | ACS 2020–2024 B25044, owner plus renter households with no vehicle |
| Lower-income block group | median household income ≤ 80% of the state median, or ≥ 20% of people below poverty (C17002) |
| Town | county subdivision of the block group's own county containing its centre of population (otherwise the one overlapping it most) |

**Wording.** "Low walking access", not "food desert". "SNAP authorization ended", not "closed".

**Known limits.**
- **Bridges and islands.** Bridge walkways missing from TIGER (above) make some river crossings and islands unwalkable. New York's health report fails for this reason: 11 island block groups (Governors, Randalls and Wards, Fire Island, the Thousand Islands, and others) with 28 car-free households have no walkable path to a store.
- **SNAP as the store source.** SNAP authorization stands in for being open: a store that never took SNAP is missing, and an end date can lag the real closing.
- **Store types.** Store-type classes are USDA's: some warehouse clubs count, and a few small grocers may be under-classed.
- **One point per block group.** One centroid stands in for every household in a block group.
- **Sidewalks.** TIGER does not map sidewalks.
- **Fixed population.** Population and households are held at 2020–2024 levels, so changes over time reflect store changes only.
- **Revised Suffolk block groups.** In New York, 39 Suffolk County block groups with a 2020 centroid have no ACS row (the ACS uses revised block groups there).

## Checks on every run

The site shows a banner when any check fails. The checks are:
- populated block groups whose snapped point is in the network's largest connected part (≥ 95%);
- share of car-free households in block groups more than 500 m from the network (≤ 1%);
- car-free households in block groups with no path to any store (0; block groups listed by ID);
- block group-years where the walk is shorter than the straight line to the nearest open site (0);
- agreement between the two distance computations (shortest-path tree and nearest-two table) within 2 miles (0 mismatches);
- change in total walkable length since the previous run (≤ 5%);
- full-service records without coordinates (≤ 2%);
- age of the SNAP file (≤ 550 days);
- ACS and TIGER vintages (no more than 3 years old);
- every ACS block group matched to a centroid.

Every run is appended to `data/runs.jsonl` with source hashes. The first independent review rebuilt the network and distances for 126 New Jersey block groups and matched within the 25 m tolerance.

## Reproduce

```
pip install -r requirements.txt
python3 src/fetch.py NJ     # sources: ~1 GB cached in data/cache for all four states; state extracts in data/raw/<STATE>
python3 src/build.py NJ     # NJ ~5 min, PA ~20 min, NY ~16 min, DE ~1 min; 2–5 GB of memory
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
