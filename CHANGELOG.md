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
