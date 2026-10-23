# Changelog

Versions follow [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0 → 2.0.0): anything that could turn the same test data into a different verdict through a looser rule, or change what `apply` writes to your files.
- **Minor** (0.1.0 → 0.2.0): new strategies, engines or commands. The verdict rule stays as strict or gets stricter.
- **Patch** (0.1.0 → 0.1.1): bug fixes and wording.

`python skills/say-my-name/scripts/smn.py --version` prints the installed version.

## [0.1.0] - 2026-10-24

First version: `prep`, `test`, `variant`, `report`, `apply` and `undo`, with a simulated answer engine (Claude through the Claude Code CLI) and paired significance tests.

Measured before release (see [bench/](bench/)):
- **Lab self-test** in English and Persian. An identical copy never wins, a planted improvement always wins, a stripped page never wins, and repeated runs land within 10 points.
- **12 live pages** in 6 niches (7 English, 5 Persian), with 720 answers. The identical-copy control gave 0 wins out of 12. Real rewrites gave 4 wins out of 24, and none made a page worse.

What the data changed:
- **The verdict also tests quote share.** In the lab, the planted improvement was already cited 87–90% of the time, so citation couldn't rise any further, but the page supplied twice as much of each answer. A citation-only test called that "no difference". There are now two paired tests (citation, and quote share), each at p < 0.025, to keep the overall false-win rate under 5%. This rule was chosen after seeing the lab data, so it was checked on fresh data: 0 false wins in 16 identical-copy controls across the pilot and the full run.
- **The engine runs with its own short system prompt, no tools and no prompt cache.** In the pilot, each call carried Claude Code's own ~25k-token system prompt and paid to write a cache that was never read: $0.166 per call against an estimate of $0.03–0.08. Calls now cost $0.04–0.06, and the estimate is computed from token counts.
- **A test stops when the account's usage limit is hit.** Before, the remaining calls were skipped one by one and partial results were saved.

Fixed during testing:
- Two `apply` runs in the same second could overwrite the original's backup. Backups now get a microsecond timestamp plus a uniqueness check.
- Persian pages typed on an Arabic keyboard (ي/ك) weren't detected as Persian.
- Brand matching missed spelling variants with a space, a ZWNJ or no gap at all (حساب يار / حساب‌یار / حسابیار).
- Words in neighbouring HTML tags ran together.
- Gzipped pages that didn't say they were gzipped came out as garbage.
- Verbatim quotes with a curly apostrophe were flagged as invented.
