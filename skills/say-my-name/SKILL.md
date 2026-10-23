---
name: say-my-name
description: Tests whether an AI answer engine would cite a page, by putting it next to real competitor pages for real buyer questions, then writes rewrites and keeps only the ones that measurably win (paired, significance-tested). Persian/RTL-ready. Use when the user asks "will AI cite my page", "why does ChatGPT/Claude recommend my competitor", "test this page for GEO / AEO / AI visibility", "make AI mention my brand", "بهینه‌سازی برای هوش مصنوعی", or wants to improve a landing page, product page or article for AI answers.
---

# Say My Name

The goal: when someone asks an AI which product to pick, it says your name, and it says it because your page earns it. You never claim a rewrite helps without the test showing it.

`SMN` means `python <this skill's folder>/scripts/smn.py` (use `python3` if needed). It needs Python 3.10+, stdlib only. All state lives in `./.smn/`.

## Rules
- **Measure, don't guess.** Every recommendation comes from `SMN report`. Rules of thumb only suggest which variants to try.
- **Never invent facts.** A rewrite may reorder, clarify, shorten and restructure. It may add a number, quote or claim only if the user gave it, or if it's on their page or in `--facts`. Show every item that `SMN variant` flags, and ask the user.
- **Ask before spending quota.** Run `SMN test NAME` (no `--yes`) first, show the user the number of calls and the cost, and add `--yes` only after they agree.
- **Never edit a live website.** `SMN apply` changes only a local .md/.mdx/.txt page, and only after the user has seen the diff and said yes.
- **Say what the test can't show** whenever you report: it's a simulated engine. It measures citation once the page is among the sources, not whether a live AI search finds the page.
- Talk to the user in their language. Write the buyer questions in the page's language.

## Steps
1. **Gather** with the user:
   - the page: a local file, or a URL (it is read only, never changed)
   - every spelling of the brand (for example `Acme` and `آکمه`)
   - 3 to 8 real buyer questions the page should win, in the page's language ("best X for Y", "X vs Y", "how do I…")
   - 3 to 6 competitor pages that answer the same questions. Suggest some by searching the web, and let the user confirm the list.
2. **Prep:** `SMN prep --page P --brand B [--brand B2] --question Q ... --competitor C ... [--runs 5] [--facts FILE]`. Read the summary, and point out any Persian issues it lists (Arabic ي/ك, spaces instead of ZWNJ, mixed digits).
3. **Baseline:** `SMN test` to show the estimate, then, after the user's OK, `SMN test --yes`.
4. **Variants:** write 2 to 4 rewrites of the page text into files, each testing **one idea** from [references/strategies.md](references/strategies.md), so a win can be explained. Store each one with `SMN variant NAME --from FILE`. Show the user anything it flags as possibly invented, and drop or fix it.
5. **Test the variants:** for each one, get the estimate, the user's OK, then `SMN test NAME --yes`.
6. **Report:** run `SMN report` and explain it plainly. A variant counts as a win only if the report says **WIN**. If nothing wins, say so: "keep your page; none of these rewrites measurably helped". That's a useful result too.
7. **Apply (optional):** run `SMN apply NAME` to show the diff. Write it only after the user says yes, with `SMN apply NAME --yes`. Tell them `SMN undo` restores the original byte for byte. For a URL or HTML page, hand over the winning text from `.smn/variants/NAME.txt` and let the user publish it.

## Reading the report
- **cited:** the share of runs that cited the page.
- **quote:** how much of the answer's wording came from the page, with earlier sentences weighted more.
- **brand:** the share of answers that named the brand.
- **avg #:** the page's average position among the cited sources.
- **verdict:** two paired tests on the same questions, competitors and shuffles: one on citation, one on quote share. Each must reach p < 0.025, which keeps the overall false-win rate under 5%. WIN means at least one measure improved and neither got worse. If the page is already cited almost every time, citation can't rise any further, and the gain shows up in quote share: the page supplies more of the answer. Anything else is "no measurable difference" or "mixed". With few runs, small gains will show as "no measurable difference". Offer more `--runs` if the user wants a sharper answer.
