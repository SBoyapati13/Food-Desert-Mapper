# Walking access to full-service food stores: New Jersey

**Live map:** https://sboyapati13.github.io/Food-Desert-Mapper/

For every census block group in New Jersey, the walking distance along streets and paths from where its people live to the nearest full-service food store, at the end of each year from 2015 to 2025. The focus is on households without a car, for whom walking distance is the binding constraint.

Built from public data that exists for every state (USDA SNAP retailer records, Census ACS, Census TIGER streets), so other states can be added by configuration. New Jersey is the first.

## Findings (stores open at 31 December 2025)

- **98,560 households without a vehicle (25% of 389,559) live in block groups more than a 1-mile walk from a full-service store.** 54% are more than half a mile away.
- **42,739 of them (43%) are in lower-income block groups.** Lower-income block groups hold 61% of the state's car-free households, but because most of them are in dense cities, a smaller share of them are beyond a mile (18%) than car-free households elsewhere (37%). The households beyond a mile are spread through suburban and rural towns, where a car-free household is rarer but further from a store.
- **Full-service store sites rose from 989 at the end of 2015 to 1,078 at the end of 2025**, and the number of car-free households beyond a mile fell only slightly (101,616 to 98,560). 188 block groups moved beyond a 1-mile walk over the decade (8,697 car-free households) and 230 moved within it (11,753). One example: downtown Millville's walking distance rose from about 0.4 km to 2.4 km at the end of 2021, when the SNAP record for its Save-A-Lot ended.
- 378 block groups are within a mile of New York, Pennsylvania or Delaware, where stores across the line are not counted. Excluding them, 90,589 car-free households are beyond a mile.

These are estimates from 5-year ACS samples at the block-group level. Margins of error on household counts are large for individual block groups (they are shown on the map); no combined margins are computed for the town or statewide totals.

## Method (v1.1)

Registered in [CHANGELOG.md](CHANGELOG.md) before any distances were computed; implementation details left open by the registration were also written down before the first run. An independent review of the first run confirmed the distances and figures and found six problems, corrected as v1.1 and labelled in the changelog as changes made after results were seen. Their effect on the published numbers was one store site and a handful of block groups.

| | |
|---|---|
| Full-service store | SNAP-authorized retailer of USDA store type Supermarket, Super Store or Large Grocery Store |
| Open on a date | authorization date on or before it, end date blank or after it |
| Store site | records within 50 m (great-circle) of each other are one site (owner changes are not closures) |
| Walking network | TIGER/Line 2024 edges: secondary roads, local streets, service drives, walkways, stairs, alleys, private roads, parking-lot roads, bike and bridle paths; excludes limited-access highways and ramps; two-way; the same network for every year |
| Where people are | 2020 population-weighted centre of each block group |
| Walking distance | shortest network path to the nearest open site, plus straight-line snaps to the network at both ends |
| Low walking access | over 1 mile (1,609 m); 0.5 mile also reported |
| Households without a vehicle | ACS 2020–2024 B25044, owner plus renter households with no vehicle |
| Lower-income block group | median household income ≤ 80% of the state median, or ≥ 20% of people below poverty (C17002) |
| Town | county subdivision of the block group's own county containing its centre of population (otherwise the one overlapping it most) |

**Wording.** "Low walking access", not "food desert": the measure covers one store type, on foot, from a block group's centre.

**Known limits.** Stores in other states are not counted (border block groups are flagged). SNAP authorization stands in for being open, and a store that never took SNAP is missing; a SNAP end date can also lag the real closing (Salem city's last grocery closed in 2017 by press accounts, but its SNAP record ends in September 2018). Store-type classes are USDA's: 48 of the 1,078 full-service sites open at the end of 2025 are membership warehouse clubs only (Costco, BJ's, Sam's Club), a few records classed as supermarkets are not conventional grocers, and some small grocers may be under-classed. One point stands in for every household in a block group, which matters most in large rural block groups. TIGER does not map sidewalks, so a road may count as walkable when it isn't safe to walk. Population and households are held at 2020–2024 levels for every year-end, so changes over time reflect store openings and closings only.

## Checks on every run

The build reports a failure (and the site shows a banner) when any of these fail: share of populated block groups whose centre is more than 500 m from the network (≤ 1%; currently 0.6%), share of the network in its largest connected part (≥ 95%; 99.7%), change in total walkable length since the previous run (≤ 5%; 76,525 km), full-service records without coordinates (≤ 2%; 8 of 2,101), block groups with no path to any store (0, listed by ID if any), block group-years whose walking distance is shorter than the straight line to the nearest open site (0), age of the SNAP file (≤ 550 days), ACS and TIGER vintages no more than 3 years old, every block group matched to the ACS. Every run is appended to `data/runs.jsonl` with the source hashes.

The walk is longer than the straight line, as it should be: at the end of 2025, walking distance divided by straight-line distance to the nearest open site has a median of 1.39 and a 90th percentile of 1.93 across block groups (minimum 1.001; the maximum, 9.9, is a block group whose nearest store is across water or a highway with no nearby crossing). An independent rebuild of the network and distances for 126 block groups matched within the 25 m tolerance.

## Reproduce

```
pip install -r requirements.txt
python3 src/fetch.py NJ     # downloads sources (about 260 MB cached in data/cache, state extracts in data/raw/NJ)
python3 src/build.py NJ     # about a minute: out/NJ/{bg_access,sites,towns,years}.csv, summary.json
python3 src/web.py NJ       # docs/ site
```

A scheduled GitHub Action (`.github/workflows/update.yml`) checks the sources monthly, rebuilds when one changes, and redeploys the site. Rebuilding from the same sources gives byte-identical block-group results.

**Adding a state:** add it to `config/states.json` (FIPS code and the two lower-income thresholds) and run the three commands with its postal code.

## Files

- `out/NJ/bg_access.csv`: one row per block group, walking distance in metres at each year-end (`walk_2015` … `walk_2025`), households, no-vehicle households and margin, income, poverty, town, border distance
- `out/NJ/sites.csv`: every full-service store site, with the years it was open
- `out/NJ/towns.csv`: towns, latest year-end
- `out/NJ/years.csv`: statewide measures by year-end, and counts of every SNAP store type
- `data/raw/NJ/manifest.json`: every source URL, size, Last-Modified date and SHA-256

## Sources

USDA Food and Nutrition Service, Historical SNAP Retailer Locator Data. U.S. Census Bureau: American Community Survey 2020–2024 5-year estimates (B01003, B25044, B19013, C17002); 2020 Census centers of population by block group; TIGER/Line 2024 edges and state boundaries; 2024 cartographic boundary files. Map tiles © OpenStreetMap contributors.

## Earlier version

v0 was a Streamlit app that mapped OpenStreetMap grocery stores around a chosen city. It is kept, unchanged, in [`legacy/streamlit_v0/`](legacy/streamlit_v0/).

Corrections and questions: [open an issue](https://github.com/SBoyapati13/Food-Desert-Mapper/issues).
