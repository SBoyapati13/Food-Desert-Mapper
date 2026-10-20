# HEFSP site extraction, part 2: notes

Output file: `sites_part2.csv` (36 data rows). I read every document through WebFetch's text extraction. Those summaries gave page references only as court e-filing stamps ("Pg X of N") and printed page footers. Where a true PDF page index could not be determined, the CSV says so. Quotes were requested verbatim and are at most 20 words. Where two fragments were needed, `...` joins them.

**Access problems.** WebFetch requests to some URLs were blocked by an unanswered permission prompt. The Jackson and Monroe URLs you supplied were blocked on the first try. Both later became reachable once they appeared in search results. These stayed blocked or unreadable:
- the Linden Google Drive HEFSP folder
- the Linden June 2025 adopted HEFSP (`library.njcourts.gov/.../linden-city/61125LindenAdoptedHEFSPPart1.pdf`, a constructed URL)
- the NJ Courts Middlesex county listing page (fetch error)

| Town | Rows | Sum of affordable_units | Fourth Round prospective need in plan |
|---|---|---|---|
| Jackson twp | 17 | 1,000 | 1,000 |
| Linden city | 12 | 583 | 756 (RDP 23 + unmet need 733) |
| Monroe twp (Middlesex) | 2 | 95 | 460 (credits) |
| Wall twp | 5 | 515 | 650 (+58 Third Round gap; Table 3 totals 708.5 credits) |
| Edison twp | 0 | — | plan not found |

---

## Jackson township (Ocean)

**Document used.** "Township of Jackson Housing Plan Element & Fair Share Plan, Fourth Round (2025-2035)", July 2025, prepared by CME Associates, from the town copy at https://jacksontwpnj.net/DocumentCenter/View/17679/2025-Jackson-HEFSP-FINAL-DRAFT.
- The town copy is titled "FINAL DRAFT", so the CSV marks it `draft`.
- The same July 2025 plan was filed with the court on 07/29/2025 (OCN-L-000336-25, `HEFSPPt1.pdf`). Only the cover and table of contents of that filing were readable; the site pages are in later parts that could not be located.
- A Pinelands Commission slide deck (2026-01-30) says the plan was adopted 7/28/2025 and lists no later amendment.

**Prospective need.** 1,000 units: "The Township has a Fourth Round (2025 – 2035) Prospective Need Obligation of 1,000 affordable units." (printed p. 32). Present need is 186 (rehab), which is excluded. No vacant land adjustment or RDP is mentioned.

**Rows.** All 17 Table 23 mechanisms ("Round IV Compliance Mechanism Summary", printed p. 34; total row "TOTALS 1,000 1,000"). They sum to 1,000, which equals the need. The plan claims no Fourth Round bonus credits.

**Pages.** Pages are printed page numbers only; the extraction did not expose the PDF page index.

**Ambiguities**
- **Hawkins:** the heading says Block 18201 Lots 17-25. The extraction reported that the site map labels reference Block 22111 Lot 1.01, which conflicts with the heading.
- **Whitesville Road Concept Plan:** the plan says "Block 22102 Lots 1 & 2 and several others". The lot list is incomplete in the source itself.
- **Viviano Properties:** the text includes "Block 22801 - South Hope Chapel Road" with no lot.
- **Grawtown:** the site has 291 affordable units. Of those, 195 count toward Round 4 and 96 toward the Third Round; I recorded only the 195. The plan also contradicts itself on project size (1,455 vs 1,344 units). The Jan 2026 Pinelands deck shows a revised 962 units / 195 affordable.
- **White Road-Faraday:** the count of 11 comes from Table 23 and the site heading. The unit sentence in the body text was not extractable.
- **Bennett Mills Road:** its page (printed p. 41) is inferred from sequence.
- **Proposed status:** most sites are inclusionary proposals. Five of them depend on overlay zoning still to be adopted: Whitesville, Butterfly, Viviano, Grawtown, and White Road-Faraday (listed "Status – Proposed").

**Excluded.** Prior-round projects (Table 21), Third Round mechanisms (Table 22), and the 186-unit rehab program.

## Linden city (Union)

**Document used.** The most recent plan: "Master Plan Amendment to Housing Element and Fair Share Plan", City of Linden, dated Feb 24, 2026 and adopted Mar 10, 2026. It amends the June 10, 2025 adopted HEFSP after a December 2025 mediation with FSHC; the Program recommended approval and the court accepted it.
- URL: https://library.njcourts.gov/files/civil/affordable-housing/union/linden-city/31326LindenAmendedPlanPart1.pdf?VersionId=bEHMKp8ooa0hfUPHIChAMtVCKrvX4ZqL
- I could not read the original June 2025 plan (blocked; see above).

**Prospective need.** 756 (mediated down from 787). A Vacant Land Adjustment gives an RDP of 23 and an unmet need of 733. The document is internally inconsistent here:
- Section C says unmet need is 1,517.
- Appendix A cites a "combined prospective need obligation" of 1,540.
- I used 756 / 23 / 733 from Section 2 and Table 12.
- The mediation also folds the prior-round (209) and Third Round (575) obligations into the Fourth Round. They have no separate mechanisms, so they are not counted here.

**Rows.**
- Three RDP sites: 10 + 12 + 1 = 23, which equals the RDP.
- Nine unmet-need mechanisms from "Table 12: Summary of Round 4 Unmet Need Compliance": 560 credits.
- Total in the CSV: 583.

**Pages.** I give the court stamp "Pg X of 25". Printed page = stamp − 1 is inferred from the table of contents.

**Problems**
- **Downtown Overlay (AHO-1, 283 units) and ROC Overlay (AHO-4, 49 units):** the plan says "Multiple Block and Lots – See Map 2 and Table 1", but Table 1 and Map 2 were not in the extracted text. Block and lot are left blank; these are defined-location overlays whose lots I could not read.
- **West Elizabeth Avenue Redevelopment Overlay (AHO-5, up to 97 units):** no block, lot, or address in the text. The plan itself says "high probability that the entire area will not be redeveloped".
- **Label and lot conflicts:**
  - AHO-3 is used for two different overlays.
  - South Wood Ave (Block 448) is described as placed in both AHO-1 and AHO-5.
  - 208-210 S. Wood is "Lots 1 and 2" in the text but "Lot 2.01" (RDP 9.11) in Appendix A.
  - Chandler lists 9 lots in the text but 4 in Appendix A.
- **Existing redevelopment plans:** Amici's (4) and South Wood Ave (16) rely on existing redevelopment plans. I included them because the plan counts them for new units toward unmet need.

**Excluded.** Present need of 299 (county and rental rehab). The general 20% set-aside ordinance has no fixed site and no unit count.

## Monroe township (Middlesex)

**Document used.** Court-filed Fourth Round HEFSP, MID-L-000638-25, e-filed 06/27/2025 (102 pp.).
- URL: https://library.njcourts.gov/files/civil/affordable-housing/middlesex/monroe-twp/HEFSPFORFILING.pdf?VersionId=0yJT6aMZJIfBDUPNZjG7wQSA9jFUTrKE
- The document you supplied (monroetwp.com/images/Monroe_2025_Housing_Element.pdf) is the same plan, marked DRAFT, with an identical Table 26.
- No Planning Board adoption date was visible in the filed copy.
- Be careful: the Pinelands and monroetownshipnj.org documents are Monroe Township in Gloucester County, not this one.

**SUPERSEDED: important caveat.** News reports (citizenportal.ai, Feb 26, 2026) say the Planning Board adopted an amended HEFSP under an FSHC settlement. I could not find that amended plan online. According to the reports, it:
- **removes** the 70 Cranbury Care Center nursing-home credits; the judge sided with FSHC
- **adds three sites:**
  - Buckelew Avenue, Block 33.03 Lots 3.01 & 3.02, 20 affordable of 67
  - Manalapan border, Blocks 36 & 36.02, 22 affordable of 100
  - former Bald Eagle site on Route 33, Block 4 Lot 14.01, 37 affordable of 186; implemented via the VC2 overlay, Ord. adopted ~May 2026

These come from news text, not the HEFSP, so they are not in the CSV. For a current-plan analysis, Monroe's rows should be treated as provisional until the amended plan is obtained.

**Prospective need.** "The Township's Fourth Round obligation is 460 units." (Pg 37 of 102, printed p. 32). Table 26 meets it with 345 units + 115 bonus = 460 credits.

**Rows (95 units).** Only the two new-construction mechanisms, under Table 26 "New Development":
- Meadowview / Project Freedom: 30 units, Block 62 Lot 3.05
- JSM: 65 units, Block 25 Lot 2.16

Bonus credits are excluded.

**Excluded and ambiguous, needing a rule decision.** Table 26's "Existing Units" credits are already built and were not previously credited. They are not *new* units, so I left them out:

| Mechanism | Units | Bonus | Location | Type |
|---|---|---|---|---|
| Valor Pointe | 43 | +43 | Block 41 Lot 14 | veterans housing; "43 Round Three units not credited previously" |
| Cranbury Care Center | 70 | +5 | Block 25 Lot 3.01 | nursing home; removed in the 2026 amendment |
| Roclene Manor | 44 | — | Block 60 Lot 15.01 | residential health facility |
| Jamesburg Manor | 43 | — | Block 76 Lot 23.04 | residential health facility |
| Waterside Villas | 13 | — | Block 27 Lot 9.04 | senior rental |
| Group Homes | 37 | +37 | no location given | group homes |

- These total 250 units.
- If your rule counts first-time credits for existing fixed-site units, the first five can be added from this table. Group Homes would still be excluded for lack of a location.
- Also excluded: the 76-unit rehab program, and prior-round and Third Round mechanisms (Tables 24-25).

## Wall township (Monmouth)

**Document used.** "Fourth Round Housing Element and Fair Share Plan", Wall Township, August 2025. The Planning Board and Township Committee endorsed it 8/25/2025, and it was filed 08/26/2025 (MON-L-000441-25) as a resubmission to the Program.
- URL: https://library.njcourts.gov/files/civil/affordable-housing/monmouth/wall-twp/82625WallLtrtoProgramresubmitFourthRoundHEFSPfinals.pdf?VersionId=6YjukLkftXp5tYElUa1qap80oW5Z_4gu
- The township's Affordable Housing Information page lists no 2026 amendment.

**Prospective need.** "The Fourth Round Prospective Need Obligation is 650," (Pg 6 of 35, printed p. 1). This was set by an FSHC mediation (Apr 2, 2025); the DCA figure was 744. The plan also carries a 58-unit Third Round gap into Round 4.

**Rows.** From "Table 3: Summary of Credits for the Fourth Round (2025-2035)" (Pg 20, printed p. 15), whose total row reads "Total 546 162.5 708.5". Five rows total 515 units:

| Site | Affordable units | Notes |
|---|---|---|
| Peddlers Village | 45 | |
| Wall Owner | 172 | 116 family + 56 senior |
| Mill Run 100% affordable | 143 | |
| Mill Run inclusionary | 123 | 47 family + 76 senior |
| Care One | 32 | assisted-living beds |

Bonus credits (162.5) are excluded.

**Ambiguities**
- **Gap vs. Fourth Round:** the plan does not say which projects cover the 58-unit Third Round gap and which cover the 650. All are listed together in the Fourth Round table.
- **Mill Run:** the 100% affordable project and the inclusionary PUD share Block 952 Lot 1 (a 386-acre parcel), so they are two rows on one lot. The 100% part is "on the western half". The Township is "actively pursuing purchase" of that part, so site control is not secured.
- **Care One:** listed as "Zoned (Executed Developers Agreement)". It also appears in the Third Round table as "0 of 32". The plan does not say whether the beds are built. I included it because it is a fixed-site mechanism not previously counted.

**Excluded**
- **Clayton Redevelopment, 31 age-restricted rental units:** these are surplus Third Round credits carried forward, and the plan gives no block or lot.
- **Rehab:** 224 units.
- **Prior Round and Third Round credits.**

## Edison township (Middlesex)

**No plan found, so there are no rows.**
- Edison filed a declaratory judgment action on 6/26/2025. The court granted temporary immunity and set an obligation schedule (hearing 10/20/2025).
- The Council's April 7, 2026 agenda (Resolution R.178-042026) says "the HEFSP was adopted by the Planning Board on March 30, 2026". It also says the court required submission by April 15, 2026.
- I could not find that plan on edisonnj.org or edisonnj.gov, or on library.njcourts.gov through search. The NJ Courts Middlesex listing page failed to load.

I did not estimate the obligation or any sites.
