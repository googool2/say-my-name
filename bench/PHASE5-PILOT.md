# Phase 5 pilot: results

This pilot follows [PHASE5-PLAN.md](PHASE5-PLAN.md), which was committed before any call. Engine: Claude Sonnet through `smn.py` 0.1.0 at commit `0d9168d`. Each condition ran 3 questions × 5 runs.

## Verdicts
| page | baseline cited / quote | aa | answer-first | structure |
|---|---|---|---|---|
| en-invoice | 87% / 0.27 | no difference | **WIN** (quote 0.36, p=0.003; up in 12/15, down in 1) | no difference (cited 100%, quote 0.31) |
| en-password | 100% / 0.52 | no difference | no difference (0.58, p=0.30) | no difference (0.66, p=0.12) |
| fa-beauty-a | 69% / 0.10 | no difference | no difference (cited 80%, quote 0.22, p=0.065) | no difference (cited 87%, quote 0.21, p=0.15) |
| fa-beauty-b | 100% / 0.36 | no difference | no difference (0.39) | no difference (0.36) |

## Pre-registered checks
- **Check 1 (false wins):** the A/A copy gave 0 WIN out of 4. On fresh data, the quote-share rule did not invent a win.
- **Check 2 (does it find anything?):** 1 WIN, 0 WORSE and 7 no-difference results among the 8 real variants.

## Notes
- Both rewrites of fa-beauty-a moved every measure the right way: citation rose from 69% to 80–87%, and quote share roughly doubled. With 15 runs per condition, that falls short of α = 0.025. More runs would settle it, but rerunning after seeing the result is not allowed under the plan.
- When the page is already cited every time (en-password, fa-beauty-b), there is little room to improve, and none of the rewrites showed a measurable gain.
- **Failures:** 7 of 240 calls failed on dropped connections and were skipped (2.9%). Since then, `smn` retries a failed call once.
- **Cost:** $38.65 for 233 answers ($0.166 per call, 83 minutes of calls). The built-in estimate had said $0.03–0.08 per call. Two things caused the gap: each call carried Claude Code's own ~25k-token system prompt and tool list, and paid to write a prompt cache that was never read. Commit `43ea382` replaces the system prompt, turns tools and caching off, and bases the estimate on token counts. The same pilot prompt now costs $0.040 per call.

## What changes for the full run
The engine settings changed after the pilot: the system prompt is now "You are an answer engine.", with no tools. That is a different simulated engine, so the full run's results are reported on their own and are not pooled with the pilot.
