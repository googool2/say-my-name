# Phase 5 full run: pre-registered plan

Written and committed **before** any full-run call. The user approved it after seeing the [pilot results](PHASE5-PILOT.md). The design is the pilot's, applied to 12 fresh pages, with the cheaper engine settings from commit `43ea382`. Results are reported whatever they show.

## Pages (12: 7 English, 5 Persian)
Each page is tested against the other pages in its niche.

| niche | pages under test | other sources in the niche |
|---|---|---|
| privacy-friendly analytics (EN) | Plausible, Simple Analytics | Fathom, PostHog |
| website builders (EN) | Framer, Squarespace | Wix, Webflow |
| time tracking (EN) | Clockify, Harvest | Toggl Track |
| project management (EN) | Asana | ClickUp, monday.com |
| anti-censorship VPN (FA) | Psiphon, Lantern, Hiddify (Persian pages) | Proton VPN free page |
| beauty stores (FA) | Yasmetic, Shimen Shop | Kaj Shop, Technolife, the author's store |

Pages were picked only because they can be fetched. Most Iran-hosted sites refuse connections from this network (1 of 50 probed answered), which is why the Persian niches are limited to sites hosted abroad and the beauty stores used in the pilot. None of these pages was a target in the pilot.

## Questions
3 per niche, in the page's language, the same for every page in the niche. They are listed in `prep.py` in the work folder and written to each page's `.smn/config.json`.

## Conditions, engine, rule
- These are the same as the pilot: baseline, aa (identical copy), answer-first, structure. There are 5 runs per question, so 12 × 4 × 15 = 720 calls.
- The variant rules are also the same: only facts already on the page, one idea per variant, and every item `smn variant` flags gets checked.
- Engine: Claude Sonnet with the system prompt "You are an answer engine.", no tools and no prompt cache. A failed call gets one retry.
- Verdict: `smn report` as committed (citation McNemar and quote-share sign test, each at α = 0.025).

## What gets reported
- **Check 1 (false wins):** WIN count among the 12 aa conditions. With α = 0.025 per test, expect 0 or 1.
- **Check 2:** WIN, WORSE and no-difference counts among the 24 real variants, split by language and by baseline citation (below 90% vs 90% or above).
- **Cost** and failed calls.
- The pilot is not pooled in, because it used a different engine setup.
