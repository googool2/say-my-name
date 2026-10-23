# Phase 5 full run: results

This run follows [PHASE5-FULL-PLAN.md](PHASE5-FULL-PLAN.md), which was committed before any call. Engine: Claude Sonnet with the system prompt "You are an answer engine.", no tools and no prompt cache (commit `43ea382`). 12 pages × 4 conditions × 3 questions × 5 runs gives 720 answers, and all 720 came back.

## Pre-registered checks
- **Check 1 (false wins):** the A/A copy gave **0 WIN out of 12**.
- **Check 2:** among the 24 real rewrites, **4 WIN, 0 WORSE, 20 no measurable difference**.

| split | WIN / variants |
|---|---|
| English pages | 1 / 14 |
| Persian pages | 3 / 10 |
| baseline cited below 90% | 1 / 4 |
| baseline cited 90% or above | 3 / 20 |

If none of the rewrites had any real effect, a false WIN would come up at most about 5% of the time per variant, so about 1 in 24. Getting 4 or more by chance has a probability of about 3%.

## Verdicts
| page | baseline cited / quote | aa | answer-first | structure |
|---|---|---|---|---|
| en-analytics-plausible | 100% / 0.47 | – | – | – |
| en-analytics-simple | 73% / 0.21 | – | – (cited 87%, quote 0.24, p=0.09) | – |
| en-pm-asana | 100% / 0.36 | – | – | – |
| en-time-clockify | 100% / 0.54 | – | – | – |
| en-time-harvest | 100% / 0.39 | – | – | – |
| en-web-framer | 87% / 0.14 | – | – (cited 100%, quote 0.22) | **WIN** (cited 100%, quote 0.20, p=0.013) |
| en-web-squarespace | 100% / 0.34 | – | – | – (quote 0.44, p=0.12) |
| fa-beauty-shimen | 93% / 0.18 | – | – | **WIN** (quote 0.25, p=0.006) |
| fa-beauty-yasmetic | 100% / 0.20 | – | **WIN** (quote 0.35, p=0.001) | **WIN** (quote 0.31, p=0.007) |
| fa-vpn-hiddify | 100% / 0.23 | – | – | – |
| fa-vpn-lantern | 100% / 0.31 | – | – | – |
| fa-vpn-psiphon | 100% / 0.30 | – | – | – |

A dash (–) means no measurable difference.

## What it shows
- **No false wins:** in 16 A/A conditions across the pilot and this run, the copy never won. The quote-share rule, which was added after the lab run, held up on fresh data.
- **Every win came from quote share.** Most pages were already cited in every run, so citation had no room to rise. What changed was how much of the answer came from the page.
- **Wins went to pages whose text was messy.** The two beauty stores' home pages are mostly product tiles and timers, and Framer's text comes mostly from interface mockups. Cleaning that text into plain statements helped. Pages that already read clearly (Plausible, Clockify, the VPN pages) gained nothing.
- **Rewrites were safe.** None of the 24 measurably hurt a page.

## Limits
- This is a simulated engine. It shows citation once a page is among the sources, not whether a live AI search finds the page.
- With 15 paired runs per condition, only fairly large gains reach significance.
- The Persian niches were limited to pages this network could reach. Most Iran-hosted sites refused the connection.

## Incidents
- The account hit its Claude session limit late in the first pass, so 77 calls failed: 48 on the limit message, 29 with an empty error. The one retry didn't help, because the limit was still in force. Seven Persian conditions were left incomplete, and they were rerun in full before anyone looked at their results. The partial files were set aside. This is why `smn` now stops when the account limit is hit.
- **Cost:** $40.47 for the 720 answers ($0.056 per call; Persian prompts use more tokens), plus $2.14 for the discarded partial runs. The pilot cost $0.166 per call.
- smn's invented-fact check flagged two quotes that were in fact verbatim. The only difference was a curly vs straight apostrophe, and the check now treats them as the same.
