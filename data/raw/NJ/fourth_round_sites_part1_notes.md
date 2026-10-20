# HEFSP site extraction, part 1: notes

Method: I read each document with WebFetch's PDF-to-text conversion and checked every row against verbatim snippets. Page numbers are printed (footer) page numbers. The text extraction carries no PDF page markers, so PDF page numbers could not be verified. Bonus credits are never counted in `affordable_units`; they appear in `units_note`.

General limitation: the WebFetch converter stops at about 100-116k characters. For Wayne and Secaucus, this cut the text off before the Fourth Round unmet-need and satisfaction sections (details below).

## Paramus borough (Bergen): 4 rows, 58 units
- **Document used:** https://www.paramusborough.gov/DocumentCenter/View/4921/Paramus-4th-Round-HEFSP-61225, the June 2025 HEFSP by DMR Architects.
  - The filename date is 6/12/25. Every page is marked "DRAFT".
  - The cover reads "Adopted by the Planning Board June 24, 2025", but the Council endorsement date is blank.
  - I recorded the status as **draft**.
  - A search found no later, court-filed, or amended version.
- **Need:** Prospective need is 1,523 per DCA, capped at 1,000. A vacant land adjustment sets the RDP at 87 and the unmet need at 229 (25% of 913). Present need is 254 per DCA, with 19 units planned for rehabilitation.
- **RDP sites:** Chart 24 (p.31) lists three sites:
  - 650 Winters Ave: 20 units
  - Ridgewood/Paramus Redevelopment: 8 units
  - Oster/Genesis additional units: 15 units
  - These total **43**. Adding the excluded 23 prior-round surplus credits and 21 bonus credits gives 87, which matches the RDP.
- **Unmet need row:** The Nursery Redevelopment Plan is recorded with an estimated 15 units. Its mechanism is labelled "UNMET NEED". It is an existing plan carried forward, and 15 is an estimate. Drop this row if the method counts only RDP mechanisms. Without it, the town sum is 43.
- **Excluded:**
  - 23 prior-round surplus credits
  - 21 bonus credits
  - HCC Zone (unmet need). It covers 559 acres along NJ-17 and NJ-4 with no block/lot or address. Its "theoretical" 2,683 units are mostly Third Round unmet-need excess.
  - The rehabilitation program
- **Ambiguities:**
  - Winters Ave: the p.27 heading says "615 Winters Avenue", while Chart 24 and p.23 say "650".
  - Ridgewood/Paramus: the p.28 heading gives Block 6701 Lot 7, while p.23 gives Lot 1. I recorded Lot 7.
  - Oster/Genesis: Chart 24 shows "≥15" (consistent with 87 = 66 + 21 bonus), but the narrative says a "minimum of 14 units". The narrative claims 1-for-1 bonuses, while the chart uses a 0.5 ratio. The site has no street address.

## Secaucus town (Hudson): 0 rows (could not read the site section)
- **Documents:**
  - The adopted Amended Fourth Round HEFSP (Clarke Caton Hintz), adopted by the Planning Board 2/17/2026 and endorsed by Council 2/24/2026. Court copy, Part 1: https://library.njcourts.gov/files/civil/affordable-housing/hudson/secaucus-town/250217AmendedSecaucusHousingPlanADOPTEDwappendicesPart1.pdf?VersionId=QN2d_8Cbok.Grku.MWmvkHNcIW6sdOmJ
  - The town's copy (footer dated Feb 6, 2026): https://secaucusnj.gov/add-public-notice/planning-board-notices/1716-amended-fourth-round-housing-element-and-fair-share-plan-2-2-1/file
- **Need:** Prospective need is 1,282 per DCA, capped at 1,000. The RDP was revised from 0 to 20 after a challenge from Fair Share Housing Center (FSHC), leaving an unmet need of 980. Present need is 25.
- **Why no rows:** Neither copy's text extraction reaches the Fourth Round section on printed pp.48-50 (Table 27, Table 28 "Satisfaction of the Fourth Round RDP", and the Fourth Round unmet-need mechanisms).
  - The town copy ends at p.42.
  - Court Part 1 ends at p.36 (stamped Pg 43 of 43).
  - I could not find a URL for Part 2.
- **What is known (not recorded):**
  - The executive summary says the RDP of 20 is met with "six senior units and 14 family rental units from inclusionary developments completed and under construction".
  - The only site listed in the table of contents under "Satisfaction of the Fourth Round Obligation" is "XChange – Inclusionary Family and Age-Restricted Rental Housing" (p.49).
  - No block, lot, or unit allocation per site was readable, so I recorded nothing rather than guess.
- **Blocked:** The council resolution URL given in the task could not be fetched at first because of a permission timeout. I later read it from a search result. It recites only the adoption and endorsement dates.

## Wayne township (Passaic): 3 rows, 142 units (167 credits)
- **Document used:** the URL given in the task, "Round Four Housing Plan… Wayne Township", dated 6/19/2025 (Kyle + McManus / T&M). Its Planning Board adoption date is blank, so the status is **draft**. A search found no adopted or court-filed version. I did not check the NJ courts Passaic County listing.
- **Need:**
  - Prospective need is 1,000. DCA calculated 1,746, which was capped. Per p.24, it includes 390 Third Round units deferred to the Fourth Round.
  - The RDP is 949: the Third Round RDP of 847 plus an additional (Fourth Round) RDP of 102 from six newly identified parcels (p.25).
  - Unmet need is not stated in the readable text. By arithmetic it would be 51, but I did not record it.
  - Present need is 162.
- **Rows:** These are the only mechanisms the plan explicitly assigns to the Fourth Round:
  - GAF: 36 of its 90 credits
  - Nouvelle: 6
  - 1805 Valley Road: 100 units (125 credits)
  - The 167 credits = the 102 additional RDP + 65 stated surplus, which is consistent.
- **Excluded:** The other 11 rows of the "Satisfaction of the 949 RDP" table (Toys R Us, AvalonBay, Preakness SC, K. Hovnanian, Waynebridge, Galreh, Summer Hill, Engel Burman, Brightview, and the two Broadway Respite group homes). The text describes them as Third Round RDP credits; p.38 says the group homes are claimed "under the Round 3 obligation".
- **Not read:** The "Satisfaction of the Fourth Round Unmet Need" section (p.42) and the Fourth Round distribution table (p.45) are cut off; the extraction ends at p.40. Any Fourth Round unmet-need overlay or redevelopment sites are therefore **missing**.
- **Ambiguities:**
  - Nouvelle's address is "993 Route 23" on p.39 but "933 Route 23" in the p.25 table.
  - Page 1 calls Wayne "Hunterdon County", which is a typo in the source.

## Roxbury township (Morris): 0 rows (plan not found)
- The plan exists: the Planning Board adopted it on 6/18/2025. The court library holds the adopting resolution (Schedule A, docket MRS-L-000250-25, filed 6/25/2025): https://library.njcourts.gov/files/civil/affordable-housing/morris/roxbury-twp/Untitled2.pdf?VersionId=Sj5j7nNMKfE8evNntBrqE9HL.PV_q1yx
- **Not found:** The plan document itself. Several searches (roxburynj.us DocumentCenter, NJ courts library, Highlands Council) did not turn it up.
- **Blocked:**
  - roxburynj.us home page: permission timeout
  - Roxbury agenda PDF: disallowed by robots.txt
  - Highlands Roxbury page: permission timeout
- **Context only, not used for rows:** The Morris County Planning Board report of 6/19/2025 summarizes the plan as present need 59, prospective need 499, a Highlands-based RDP of 12.5, and an unmet need of 486.5. It says "Five new sites have been identified" but does not name them.

## South Brunswick township (Middlesex): 14 rows, 619 units
- **Document used:** the URL given in the task, the January 2026 HEFSP by Alaimo Group. The Planning Board adopted it on 1/28/2026 and the Governing Body endorsed it on 1/29/2026 (per the cover), so the status is **adopted**. The plan implements the 2024 FSHC settlement.
- **Need:** Prospective need is 1,070 per the settlement (DCA: 959), with no cap adjustment. Present need is 132.
- **Round 4 table (pp.19-20):** 920 units plus 268 bonus credits, for 1,188 credits against an obligation of 1,070 (a surplus of 118; p.22 says 119).
- **Included (619 units):**
  - Menowitz/Khov: 8
  - Sassman: 1
  - Harbor Assisted Living: 15
  - Jaynar balance: 59
  - RPM Phase I: 63
  - RPM Phase II: 70
  - Days Inn: 30
  - 4126 Route 1: 24
  - Sonesta (Block 97): 40
  - SBC: 40
  - Amato: 40
  - 4375 US-1 (Block 99): 25
  - Henderson Road: 125
  - 3674 Route 27: 79
- **Excluded (301 units; 619 + 301 = 920, which matches the table):**
  - TG/RDG Third Round surplus: 32
  - East Meadow: 6. The table labels it "Inclusionary OffSite", but the narrative describes a payment in lieu used to write down six resale units at unstated locations. That is effectively a buy-down with no fixed site.
  - Dungarvin third group home: 3, with no address (still to be acquired)
  - REACH market-to-affordable: 30 + 34
  - New Group Homes: 30, with no locations
  - Non-profit scattered-site program: 70, with no locations
  - Extensions of controls (Summerfield / Deans Pond Crossing / Monmouth Walk): 96
- **Ambiguities:**
  - The table subtotal reads 610, but the rows sum to 611.
  - 3674 Route 27 is Lot 23.201 in the table but 23.021 in the narrative. I recorded the table value.
  - RPM Phase II is 70 in the table but a "sixty unit" project in the narrative.
  - The Henderson Road narrative names only Lot 12.012 and says "126 affordable units" in one place.
  - The Summerfield extension components sum to 95 against a listed 96. That row is excluded anyway.
  - RPM has no street address.
