# HEFSP site extraction, part 4: notes

## Method
This time the PDFs were downloaded directly with curl and converted with `pdftotext` (both `-layout` and `-raw`). That avoided WebFetch's ~100k-character cutoff, which had blocked earlier parts.

- Page numbers are given two ways: the printed page and the PDF page, where the PDF page is located by form-feed count.
- Every quote was checked against the extracted text. Table quotes follow `-raw` reading order.
- Bonus credits are never counted in `affordable_units`.
- Downloaded copies are in `hefsp/dl_<town>/`.

## Summary

| Town | Rows | Units in rows | Fourth Round prospective need | Status |
|---|---|---|---|---|
| Secaucus town | 3 | 419 | 1,000 (capped); RDP 20, unmet 980 | adopted 2/17/2026 |
| Wayne township | 2 new (5 total with part 1) | 236 new (378 total) | 1,000; additional RDP 102; unmet 898 | adopted 6/30/2025 |
| Roxbury township | 4 | 11 (12.5 credits) | 499; RDP 12.5; unmet 486.5 | adopted 6/18/2025 |
| Hardyston township | 4 | 46 | 647; durational adjustment 647; overlays 46; unmet 601 | adopted (March 2026 amendment) |
| Edison township | 0 | – | not read | plan not found / site blocked |
| Franklin township | 0 | – | not read | blocked (permission not answered) |
| Toms River township | 0 | – | not read | robots.txt refusal: needs a manual download |

## Secaucus town (Hudson): 3 rows, 419 units
- **Document used:** the town copy, https://secaucusnj.gov/add-public-notice/planning-board-notices/1716-amended-fourth-round-housing-element-and-fair-share-plan-2-2-1/file. It is the full 426-page plan with appendices, and its footer is dated February 6, 2026.
- **Status:**
  - The court-filed Part 1 (HUD-L-000377-25, stamped "Adopted February 17, 2026", which ends at p.36) matches this copy word for word through p.36. The only differences are the dates.
  - I therefore treat the town copy's text as the adopted plan.
  - Court Part 2 is still not located; guessed URLs return 404.
- **Need:**
  - Prospective need is 1,282, capped at 1,000.
  - The Fourth Round RDP is 20, after the challenge from Fair Share Housing Center (FSHC). Per Table 27, it comes from three newly vacant sites:
    - Imagine Gardens, 52/4.041: 15
    - 58 County Ave, 33/4.02: 2
    - 82 County Ave, 33/11: 3
  - The unmet need is 980.
  - Note: Table 27 sites only *generate* the RDP. The plan satisfies the RDP at XChange instead (Table 28), so those three sites are not rows.
- **Rows:**
  - **XChange, family rental: 14 units, RDP.** These are 14 of the 66 remaining proposed family units. Block/lot is the full XChange footprint from p.39, because the plan does not say which phase or lot will hold them.
  - **Secaucus Junction Train Station towers: 375 units, unmet need.**
    - This is a Town request that NJSEA require a 20% set-aside on future towers.
    - The plan gives no block/lot.
  - **Transit Village Redevelopment Area, Transition Zone: 30 units, unmet need.**
    - This depends on a proposed petition to raise the zone to 500 units.
    - Block 5, Lots 7.01, 7.02, 8, 9 come from the redevelopment plan in the appendix, at PDF p.357.
- **Rows sum:** 14 RDP + 405 unmet need = 419.
- **Excluded:**
  - XChange age-restricted units, 6 of 9, status "Completed" (Table 28): these are completed units. If completed units credited for the first time to the Fourth Round are allowed, add 6, which brings the RDP to 20.
  - NJSEA Interim Rules 20% set-aside and the town-wide mandatory set-aside: mechanisms without a location.
  - The Waverton (12), the first station tower (125), and the Transition Area (70): Third Round unmet need.
  - Boulevard Tire: removed by the plan.
  - All Prior Round and Third Round credits; rehab.

## Wayne township (Passaic): 2 new rows, 236 units
- **Document used:** the adopted plan, court-filed. https://waynetownship.com/wp-content/uploads/2025/07/2025-06-30-Wayne-Twp-4th-Round-HEFSP-Reso-Filed.pdf (PAS-L-000288-25, filed 7/2/2025; cover reads "Adopted by the Planning Board June 30, 2025").
  - I diffed it against the 6/19/2025 draft. The obligation, RDP, unmet-need and distribution sections are **identical word for word**.
  - **The 3 part-1 rows (GAF, Nouvelle, 1805 Valley Road) can therefore be upgraded to status "adopted".**
  - A search of the Wayne media library found no later amended HEFSP.
- **Need:**
  - Prospective need is 1,000.
  - The additional (Fourth Round) RDP is 102, giving a total RDP of 949.
  - The Fourth Round unmet need is 898 ("1,000 total obligation – 102 RDP"). The 25% realistic-zoning requirement is 225.
- **New rows:** the PSC/WH (Preakness–Wayne Hills) overlay, printed pp.42-43, totals 236:
  - Preakness Shopping Center, Block 3205 Lot 7: 70 units. These are in addition to the 244 units already zoned there for the Third Round.
  - Remaining Area: 166 units. The plan writes the overlay as "Block 3205, Lots 1- 7; Block 3200 3-7". Lot 7 has its own row, so this row's lots are 3205:1-6 and 3200:3-7, which I derived from that.
- **Totals:** part 1 + part 4 = 142 + 236 = 378 units.
- **Excluded:**
  - **1982 Hamburg Turnpike** (Block 3517, Lots 44, 45). The Fourth Round map labels it an unmet-need site, and it carries 57 of the 102.41 additional RDP. However, the text says the Township finds it "not appropriate to rely on any affordable units from the property" while a Board of Adjustment application is pending.
  - The other additional-RDP parcels (910 Hamburg Tpk, 981 Preakness Ave, 555 Hamburg Tpk, Ratzer Rd): they only generate RDP, and the plan does not use them as compliance mechanisms.
  - North Jersey Country Club (3100/3) and 1655 Valley Road (3103/15): Third Round unmet need.
  - Mandatory set-aside ordinance: no location.
  - The text says "2 overlay zones", but only the PSC/WH overlay (with two components) is described.

## Roxbury township (Morris): 4 rows, 11 units (12.5 credits)
- **Document used:** https://www.roxburynj.us/DocumentCenter/View/6978/Roxbury-HEFSP-June-3-2025-optimized-, linked from the Planning & Zoning page. roxburynj.us robots.txt allows /DocumentCenter.
  - It is the 189-page plan with appendices, filename dated 6/3/2025.
  - It carries no adoption stamp, but the court-filed resolution shows the Planning Board adopted the plan on 6/18/2025.
  - I found no later amendment.
- **Need:**
  - Prospective need is 499.
  - The Highlands RDP is 12.5, and the unmet need is 486.5.
  - Present need is not re-checked here.
- **Rows (Table 6):**
  - Roxbury Motel: 3
  - Kenvil Hotel: 6
  - Habitat for Humanity, 270 Mount Arlington Blvd: 1, plus 1 bonus not counted
  - WNJ Realty, 725 Route 46: 1, plus 0.5 bonus not counted
  - Total: 11 units = 12.5 credits. The plan also applies 7 Third Round surplus credits (19.5 total), which are excluded.
- **Conflict:**
  - For the Roxbury Motel, Table 6 says Block 6501 Lot 17, but the narrative says "Block 6601, Lot 33.01".
  - The Township's 10/8/2025 redevelopment hearing notice (DocumentCenter/View/7084) uses Block 6501 Lot 17, so I recorded Table 6.
- **Excluded:**
  - Unmet need: only the mandatory 20% set-aside is named, and "Outside the locations listed in Table 6, the Township is not aware of any other areas likely to undergo redevelopment." No located unmet-need site.
  - Third Round surplus.
  - All Third Round mechanisms, AH-12 through AH-16.

## Hardyston township (Sussex): 4 rows, 46 units
- **Document used:** "Amendment & Supplement to the 2025 HEFSP", March 2026, 236 pages with appendices. https://hardyston.com/wp-content/documents/2026%20Amendment%20to%20the%202025%20HEFSP%20w%20Appendices.pdf
  - It implements the 12/19/2025 FSHC mediation agreement.
- **Status: adopted.**
  - The Joint Land Use Board hearing was noticed for 3/9/2026.
  - Ord. 2026-05 (AH-1) and 2026-06 (AH-2) were finally adopted on 3/11/2026. Both recite that the Board "has adopted, and the Township Council… has endorsed, an Amended Housing Element & Fair Share Plan".
  - The amendment itself shows no adoption date.
- **Need:**
  - Prospective need is 647.
  - The durational adjustment is 647, for sewer capacity.
  - The overlay zones total 46, leaving an unmet need of 601.
- **Rows:** four Route 94 overlay parcels at 6 du/ac with a 20% set-aside:
  - Block 67 Lot 2.08: 17
  - Block 67 Lot 16.03: 2
  - Block 67.05 Lot 1: 14
  - Block 67.29 Lot 1: 13
  - Total: 46
  - For Indian Field Phase 5, the table shows a 20% set-aside of 17 but "Net Additional Units" of 13. I used 13, which matches the plan's total of 46.
  - The plan gives no street addresses.
  - These parcels are developable only if sewer capacity becomes available.
- **Excluded:**
  - **Scattered Site Municipal Partnership Program** (10 township lots, 19 units, e.g. Bl 5 Lot 2 at 1 Forest Trail; Bl 63 Lots 24.07-24.14 on Wheatsworth Rd). It explicitly addresses the **3rd round** 19-unit market-to-affordable shortfall.
  - Crystal Springs Village Center amended redevelopment plan: Third Round site.
  - Mandatory 20% set-aside ordinance: no location.
  - The June 2025 plan's exclusions, from part 3, still stand.
- **Supersedes** part 3's zero-row result for Hardyston.

## Edison township (Middlesex): 0 rows (plan not found)
- **Searched with no plan found:**
  - edisonnj.org: Master Plan page, Planning & Zoning page, and homepage links
  - web search for edisonnj.org / edisonnj.gov
  - library.njcourts.gov, by search; the middlesex/edison-twp prefix did not surface
- **Site behavior:** edisonnj.org serves intermittent bot challenges (HTTP 202 with an empty body, or 403) to automated requests. The council agenda and boards pages could not be read. One WebFetch of https://www.edisonnj.org/ failed because the permission prompt was not answered.
- **Known only:** Planning Board adoption on 3/30/2026, from the part 2 notes.
- **Needs:** a manual download from the township, or a Planning Board / clerk request.

## Franklin township (Somerset): 0 rows (blocked)
- **Blocked URL:** https://www.franklintwpnj.org/home/showpublisheddocument/30943/638845570691770000
  - curl returns Akamai "Access Denied" (403) for both the document and robots.txt.
  - The WebFetch permission request was not answered in time, so it was not retried.
- **No other copy found:**
  - The NJ courts library search returns only Franklin, **Gloucester** (a different town).
  - The franklinreporter.com legal notices hold only implementing ordinances (e.g. Intro Ord 4497-26, the Chapter 81 rewrite). These are not the plan, so I did not use them for sites.
- **Still needed:** the 6/2025 plan (~650-659 units per press) and the 2/18/2026 addendum (the 55-unit Dunbar site). They need a manual download, or approval of the franklintwpnj.org fetch.

## Toms River township (Ocean): 0 rows (robots.txt refusal)
- WebFetch of https://www.tomsrivertownship.com/DocumentCenter/View/11616/Toms-River-Fourth-Round-Housing-Element-and-Fair-Share-Plan again returned **ROBOTS_DISALLOWED**.
- tomsrivertownship.com also resets connections for Claude user agents.
- I did not work around this; no curl with a spoofed user agent was used.
- **No other copy found:**
  - The NJ courts library search finds only South Toms River and other Ocean towns.
  - Searches for county, press, or state copies found none.
- **Needs a manual download.** Per part 3 news context, an amended plan was approved by Council on 4/8/2026; the court hearing was 8/26/2026.

## Blocked or unread URLs
- https://www.franklintwpnj.org/home/showpublisheddocument/30943/638845570691770000 (Akamai 403; WebFetch permission not answered)
- https://www.edisonnj.org/ (WebFetch permission not answered; curl gets intermittent bot challenge)
- https://www.tomsrivertownship.com/DocumentCenter/View/11616/... (robots refusal via WebFetch)
- https://library.njcourts.gov/files/civil/affordable-housing/hudson/secaucus-town/...Part2.pdf (not found; not needed, because the town copy is complete)
