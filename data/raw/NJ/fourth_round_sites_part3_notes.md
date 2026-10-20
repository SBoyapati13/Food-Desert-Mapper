# HEFSP Fourth Round sites, part 3: notes

Towns: Franklin (Somerset), Old Bridge (Middlesex), Hardyston (Sussex), Toms River (Ocean), West Windsor (Mercer).
Rows came from WebFetch text extraction of PDFs. Page numbers are as reported from that extraction. Quotes are as returned by the extractor; OCR spacing has been normalized where noted.

| Town | Rows | Sum of affordable_units | Plan's Fourth Round prospective need | Status |
|---|---|---|---|---|
| Franklin twp (Somerset) | 0 | n/a | not read (~650-659 per news reports, unverified) | plan NOT READ |
| Old Bridge twp | 14 | 439 (see caveats) | 673 (RDP 312, unmet need 361) | court-filed June 2025 plan; an amended plan from Sep 2026 exists but was not found |
| Hardyston twp | 0 | 0 | 647 (whole amount deferred by a durational adjustment) | adopted June 2025 plan read; 2026 amendment exists but was NOT READ |
| Toms River twp | 0 | n/a | 649 per a news report of the settlement (unverified from the plan) | plan NOT READ |
| West Windsor twp | 8 | 411 | 480 (settlement) | adopted 02-04-2026 revised plan |

---

## Franklin township (Somerset): no plan read
- Not to be confused with **Franklin Township, Gloucester County** (franklintownshipnj.org). The search results kept returning that town's HEFSP. Its sites (Block 1902 Lot 1, 1457 Fries Mill Rd, 250 credits, need 243) are NOT Somerset's and are excluded.
- Somerset Franklin's site is franklintwpnj.org. Its Affordable Housing page lists "Fourth Round Housing Element and Fair Share Plan," but the extractor did not show the link target.
- The draft 2026 master plan reexamination report, in the Feb 4, 2026 Planning Board agenda, footnotes the 4th Round HEFSP at `https://www.franklintwpnj.org/home/showpublisheddocument/30943/638845570691770000`. Fetching it was **blocked**, because a permission request went unanswered.
- The NJ Courts Somerset listing page returned a fetch error. No `somerset/franklin-twp` file turned up in search.
- Context from news, not used for rows: the Planning Board approved the plan on 6/18/2025 with "659 affordable housing units" (Franklin Reporter). The Council endorsed it on 6/24/2025. On 2/18/2026 the Planning Board adopted a Fourth Round **addendum** adding one court-required site; TAPinto describes it as a 55-unit site tied to Dunbar Homes. The council ordinance of 2/24/2026 refers to "about 650 units". A 100% senior-affordable redevelopment on Franklin Boulevard is mentioned.
- **No rows. Nothing was estimated.**

## Old Bridge township (Middlesex)
- **Document used:** "2025-2035 Housing Element and Fair Share Plan", June 2025, by Veena Sawant, PP, AICP. It is the NJ Courts e-file "copy 1 of 7", and every page carries a 06/27/2025 stamp. Status is **court-filed**; adoption is not confirmed in the text.
- **Newer version exists but was not found:** On Sep 15, 2026 the Council endorsed an **amended** HEFSP by a 7-1 vote (citizenportal.ai). I could not locate the amended document on oldbridge.com, where the document lists come back empty, or in the NJ Courts library. The Middlesex listing page returned a fetch error. **The rows may therefore be out of date.**
- **Obligation:** prospective need is 673, set by the court/Program on 4/24/2025 (DCA's figure was 685). The vacant land adjustment gives an RDP of 312 and an unmet need of 361. Rehab need of 318 is excluded.
- **How the plan meets it:**
  - Table 29 (PDF 42 / printed 41) claims 375 credits against the 312 RDP, a surplus of 63. The 375 reconciles exactly as: the full VLA RDP of 312 (private vacant 239 + public vacant 17 + under-utilized 56), plus 54 project credits (7+5+12+14+10+5+1), plus 9 rental bonuses.
  - The unmet need of 361 is addressed separately by Trekton Square, the Englishtown-Raceway Park area, the Old Bridge Transit Village, and a 26-unit special-needs project.
- **Rows:**
  - 7 named projects: Poor Farm Rd 7, Oak Tree Plaza 5, Hanley Orchards 12, Vision OB IV 14, Vision OB III 10, Geick Park 5 (+5 bonus excluded), Habitat 308 Norwood 1. Total 54.
  - 3 aggregate VLA rows: private vacant 239; public vacant (units left blank); under-utilized 56.
  - 4 unmet-need rows: Trekton 90; Englishtown-Raceway, Transit Village and special needs left blank.
  - The sum of 439 = 54 + 239 + 56 + 90.
- **Ambiguities to resolve before analysis:**
  1. **Are VLA parcels "sites"?** The plan credits the RDP parcels directly as compliance: "40 privately-owned vacant parcels (239 credits)". But it states no zoning mechanism for them. I recorded them as aggregate rows with mechanism text "vacant land RDP parcels credited as compliance" so they can be filtered out under the registered rule.
     - Their block/lot data comes from **Appendix B, the Vacant Land Analysis**, on the township's site (status unknown). In the main plan, Table 28 is garbled in extraction.
     - Per-parcel private RDP sums to 238, not 239. Under-utilized sums to 55, not 56.
     - Private sites 7 and 11 have RDP 0, and their block/lot was not captured.
  2. **Public vacant credits conflict.** Appendix B gives 17. The main-plan Table 29 extraction reads "2 credits". The units cell is left blank.
  3. **Double count.** Trekton Square (4185/13.11, 90 affordable) is also private RDP site 3 (RDP 88). In addition, 21004/2 appears both as private site 34 and in under-utilized site 3.
  4. **Vision OB III** gets 10 credits, but the text describes only 4 affordable units. There are also 6 Medicaid beds, but the plan does not explicitly tie them to the 10 credits.
  5. **Address conflicts:**
     - Vision OB IV appears as both 299-A Texas Rd and 733 Texas Rd.
     - Hanley Orchards appears as both 3 Old Mill Rd and 3 Old Rd.
     - Public site 2 appears as both E Greystone Rd and 476 Morristown Rd.
  6. **Englishtown-Raceway, Transit Village and special needs** have no affordable counts in the plan. I kept them as located mechanisms with blank units. The Englishtown lot list is OCR'd: "25.1 1" was read as 25.11; the source repeats "11 and 11"; "4 5" was read as 4;5.
  7. Several named projects date from 2017-2022 approvals: Geick Park was approved 9/7/2017 and Poor Farm on 12/1/2022. The plan credits them to the Fourth Round, and I found no statement that they were counted in the Third Round.
- **Excluded:** rehab (Home Improvement Program), the affordability assistance manual, and the 1.5 rental bonus credits carried forward.

## Hardyston township (Sussex)
- **Document used:** "2025 Housing Element and Fair Share Plan", June 2025, by Carrine Piccolo-Kaufer, PP. It was **adopted** by the Land Use Board on 6/24/2025. https://hardyston.com/wp-content/documents/2025%20Housing%20Element%20and%20Fair%20Share%20Plan.pdf
- **Obligation:** prospective need is 647, from an NJBA settlement and the 3/31/2025 order. The plan seeks a **durational adjustment for all 647**, citing sewer/water capacity (pp. 39-41). Its summary table shows "Infrastructure Adjustment -647" and "4th Round Unmet Need 647".
- **No Fourth Round sites in this plan, so 0 rows:**
  - The proposed Route 94 corridor mixed-use overlay names no lots and assigns no units. Excluded as a mechanism without a defined location.
  - The 20% mandatory set-aside is a policy, not a site. Excluded.
  - Lam Development / Crystal Springs (Block 16.31 Lot 1; 16.32 Lots 1-2; 16.33 Lot 1; 10 units) sits in the Fourth Round section, but the plan applies it explicitly "to the unmet need from the Third Round". Excluded.
  - The rental bonus table (Crystal Springs Village, Grand Cascades Lodge, Ridgefield Commons) is Third Round. Excluded.
- **Newer version exists but was NOT READ:** the Land Use page lists "2026 Amendment to the 2025 HEFSP w Appendices" at https://hardyston.com/wp-content/documents/2026%20Amendment%20to%20the%202025%20HEFSP%20w%20Appendices.pdf. A 2/19/26 master plan amendment notice is also listed. Fetching both was **blocked** because a permission request went unanswered.
  - The 2/25/2026 Council minutes (Ord. 2026-04) refer to "sites or specific zones otherwise identified in the HEFSP" and a Superior Court-approved plan. The amendment may therefore add Fourth Round sites. **The zero-row result covers only the June 2025 plan and may be superseded.**

## Toms River township (Ocean): no plan read
- The HEFSP is on tomsrivertownship.com: DocumentCenter/View/11616, "Toms River Fourth Round Housing Element and Fair Share Plan" (Alaimo Group). There is also an "Amended Housing Element and Fair Share Plan" at DocumentCenter/View/344, whose round is unknown. **Every fetch of tomsrivertownship.com was refused (robots.txt disallowed).**
- The NJ Courts Ocean listing shows only "Municipal Resolution January 30, 2025" for Toms River. No HEFSP was found in the library.
- Context from news, not used for rows:
  - A mediation agreement with FSHC was filed 12/8/2025 and approved by Council on 12/10/2025 (Patch): prospective need 649, present need 526.
  - Mechanisms named in that coverage: Hope's Crossing (110 + 83.25 bonus), 2008 Route 37 LLC (4 affordable), Route 70 properties (134), Jamestowne Village (42), and extensions of controls.
  - Hope's Crossing later withdrew, and the plan was revised: two township-owned Route 9 sites, Route 70 West 134, Jamestown 48, a Route 37 conversion. Council approved it on 4/8/2026 (Shore News Network, "186 affordable units").
  - The court extended immunity on 7/9/2026, with a hearing set for 8/26/2026.
  - The mediation agreement is on Scribd (not an HEFSP; not read).
- **No rows. Nothing was estimated.**

## West Windsor township (Mercer)
- **Document used:** "2026 Housing Element & Fair Share Plan" (Master Plan Section IV, Revised), **adopted 02-04-2026** by the Planning Board (Appendix A-2). It supersedes the plan adopted June 25, 2025, which had an RDP of 238.
  - The main PDF's text extraction stops at printed p. 67, partway through §4.4, so §4.5 "Fourth Round Components" (pp. 83-107) was unreadable.
  - Site rows were therefore taken from **Appendices 01 → Appendix C (Fourth Round Settlement Agreement with FSHC), Exhibit A**. Exhibit A gives block/lot, location and units per site.
  - The units match HEFSP body Table 4 (printed p. 12): 411 units + 96 bonus = 507.
- **Obligation:** prospective need is 480 under the FSHC settlement (DCA 661; township's own figure 392). No VLA/RDP is applied in the settlement. Rehab of 4 is excluded.
- **Rows:** 8 sites, sum 411 affordable units, or 507 with the 96 bonus credits. This exceeds 480 by 27 per the plan.
- **Page numbers:** these are Exhibit A printed pages. Sequential PDF pages could not be determined from the extraction.
- **Ambiguities:**
  - **Eden – Oak Lane** (313 Oak Lane, Block 35 Lot 17, 4 credits) is an **existing** Eden Institute group home, newly credited to the Fourth Round. It is included as a fixed-address group home, but flagged; drop it if "new units" is read strictly.
  - **BXP 901 Series** is flagged "Potential" for age-restricted use.
  - Exhibit A's 901 Series "four-prong test" text refers to the 400 Series. This looks like a drafting error.
  - Most sites have intersection descriptions, not street addresses.
- **Excluded:** Third Round and prior-round components, special needs and market-to-affordable (§4.4), and the bonus credits (recorded only in units_note).

## Blocked or unreadable URLs (for re-try with permission)
- https://www.franklintwpnj.org/home/showpublisheddocument/30943/638845570691770000 (Franklin Somerset Fourth Round HEFSP, presumed)
- https://hardyston.com/wp-content/documents/2026%20Amendment%20to%20the%202025%20HEFSP%20w%20Appendices.pdf
- https://hardyston.com/wp-content/documents/land_use/2-19-26%20lglnts.mstrpln.amnmn.pdf
- https://tomsrivertownship.com/DocumentCenter/View/11616/Toms-River-Fourth-Round-Housing-Element-and-Fair-Share-Plan (refused by robots.txt)
- https://www.westwindsortwp.gov/agenda_detail_T12_R271.php (blocked; not needed)
- West Windsor main HEFSP §4.5 (printed pp. 83-107): beyond the extraction cap
- NJ Courts county listing pages (middlesex, somerset): fetch errors
