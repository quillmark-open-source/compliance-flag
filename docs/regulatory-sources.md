# Regulatory Sources

The beta package currently includes regulatory source files migrated from the alpha scanner. Before the first public release, each bundled source should be checked for:

- authoritative source URL
- retrieval date
- redistribution terms
- whether it should be bundled, linked, or fetched by a separate setup step

Bundled scan-time sources:

- SEC Rule 275.206(4)-1, Investment Adviser Marketing
- SEC Rule 275.204-2, Books and Records
- SEC Part 279, Forms Under the Investment Advisers Act

These files are included with captured source content in scan prompts so Anthropic's Opus model can draft findings against the current SEC Marketing Rule focus.

## Current-As-Of Notes

The bundled `sec-rule-275-206-4-1-investor-marketing.md` source text is labeled by eCFR as "up to date as of 2/23/2026" and "17 CFR 275.206(4)-1 (Feb. 23, 2026)." In the legacy engineering repository, this file first appears in commit `e5d3634aed51292d63a1fe5bcf3fd21134447b57` dated 2026-04-04.

For now, treat the bundled scan-time regulatory sources as current as of 2026-02-23 unless a newer source date is documented for a specific file.

Do not add new regulatory materials without documenting source provenance here.
