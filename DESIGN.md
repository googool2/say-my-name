# Say My Name: design (phase 1)

**One line:** test whether an AI answer engine would cite your page, before you publish, and keep only the rewrites that measurably win.

## The job
Existing GEO tools score pages against rules of thumb ("add statistics", "answer first"). Research from 2026 shows those rules don't reliably raise citations, and sometimes lower them. Say My Name replaces the guess with a controlled test on the user's own page, against real competitor pages, for the user's own buyer questions. It's Persian-ready from day one.

**For:** marketers, founders, agencies, and anyone writing pages they want AI assistants to cite. That includes Persian, Arabic and other RTL content.

**Triggers:** "will AI cite my page", "test this page for GEO", "make ChatGPT/Claude mention my brand", "why does AI recommend my competitor", "AI visibility of this page", "بهینه‌سازی برای هوش مصنوعی", "GEO".

**Not doing (other tools already do these well):** full-site SEO audits, crawler and `llms.txt` checklists, schema generators, live rank or brand-mention tracking. The README links to them.

## How it works
`SMN` = `python scripts/smn.py`. The script is stdlib only, and is deterministic except for the model calls.

| Step | Command | What happens | Changes files? |
|---|---|---|---|
| 1. Collect | `SMN prep` | Reads your page (a local file or a URL) and the competitor pages (URLs you approve; Claude may suggest some via web search). It extracts the main text and splits it into passages. Persian checks run here: Arabic ي/ك versus Persian ی/ک, broken or missing ZWNJ, mixed digits. Brand-name variants are recorded (Latin and Persian spellings). | only `.smn/` |
| 2. Baseline | `SMN test` | For each question, the model gets the question plus all sources **in a shuffled order with neutral ids** (S1…Sn) and must answer with citations. This repeats R times per question. | only `.smn/` |
| 3. Variants | Claude writes 2 to 4 rewrites of your page | Strategies are drawn from the research (answer-first, statistics, quotations, clear entity statements, Persian normalization), but none is assumed to work. Facts are never invented: new numbers or quotes must come from you or your sources. | only `.smn/` |
| 4. Compare | `SMN test --variant V` | Each variant is tested with the **same questions, competitor set and shuffle seeds** as the baseline, so the comparison is paired. | only `.smn/` |
| 5. Decide | `SMN report` | A variant "wins" only if it beats the baseline on citation rate with a paired test (p < 0.05) and doesn't lose on the other metrics. Otherwise the report says **"no measurable gain, keep your page"**. | no |
| 6. Apply | `SMN apply V` / `SMN undo` | Shows a diff and writes the winning text into your file **only with your OK**. It keeps a byte-exact backup, and `undo` restores it. Live websites are never edited. | your file, after a yes |

**Metrics per question and engine:** *citation rate* (share of runs citing your page), *first-citation position*, *quote share* (how much of the answer's wording comes from your page, weighted by position, as in the GEO paper), and *brand mention* (your name appears in the answer text).

**Engines:** by default, headless `claude -p` on the user's own Claude Code login, with no API key needed. If the user sets `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` or `GEMINI_API_KEY`, it can also run on those models. With more than one engine, a variant must win on the majority of them. Before any test runs, the script prints an estimate of the number of model calls and the cost, and nothing runs without a yes.

## Safety and honesty rules
1. **The engine is simulated, and every report says so.** The lab measures "when your page is among the sources, how likely is it to be cited and quoted". It doesn't measure whether ChatGPT retrieves your page in the first place.
2. **No invented facts in rewrites.** A rewrite can't add numbers, quotes or claims the user didn't provide. The report flags every new number for the user to check.
3. **Paired, repeated, significance-tested.** No "it went from 2/5 to 3/5, so it's better".
4. **Never edit a live site.** Only local files are changed, with a diff, a yes, a backup and undo.
5. **Privacy:** pages and questions go to the chosen model provider. The README states this, and competitor pages are fetched politely (with a user agent, at a slow pace, honoring `robots.txt`).

## How we'll know it works (phases 3 to 6)
| # | Test | Pass bar |
|---|---|---|
| 1 | **A/A test:** baseline versus an identical copy | "No difference" in at least 95% of runs (false-win rate ≤ 5%) |
| 2 | **Planted-signal test:** a version that adds the exact answer to the question, versus one that removes it | The lab detects the planted difference in at least 90% of runs |
| 3 | **Repeatability:** the same test twice | Citation rates within ±10 points |
| 4 | **Real pages:** about 10 English and about 10 Persian pages from different fields | Report the share of pages where a variant measurably wins, and the median gain, **whatever it turns out to be** |
| 5 | **Safety:** `apply` then `undo` | Byte-identical; nothing outside the target file changes |
| 6 | **Cost:** calls and tokens per test | Published in the README |

## Packaging (same as Thanks Mom)
`skills/say-my-name/` (SKILL.md, `scripts/smn.py`, `references/strategies.md` with the research summary and citations), `.claude-plugin/`, CI on three operating systems, MIT, semver, and a CHANGELOG.

## Open questions for you
1. **Which engines are the default?** Claude only (no keys needed, simplest to start), or should OpenAI/Gemini also be first-class from v1?
2. **What should we test it on?** For the real-page test (#4), do you have Persian pages, your own or ones you're allowed to use, from a few different fields?
3. **Single page first?** v1 tests one page at a time. Batch mode, for a whole site, would come later.
