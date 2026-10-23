# Phase 5 pilot: pre-registered plan

Written and committed **before** any pilot call. Results are reported whatever they show; nothing below changes after the run.

## Why
The lab test showed the tool works on pages written for it. This pilot asks whether it works on live pages, and it checks on fresh data the quote-share rule that was added after the lab run.

## Pages (4)
| id | language | page under test | competitors |
|---|---|---|---|
| en-invoice | English | Invoice2go home page | FreshBooks, Wave, QuickBooks, Square invoicing pages |
| en-password | English | Bitwarden personal page | Proton Pass, Dashlane, Keeper |
| fa-beauty-a | Persian | the author's own beauty store home page | Kaj Shop, Shimen Shop, Yasmetic, Technolife cosmetics |
| fa-beauty-b | Persian | Kaj Shop home page | the author's store, Shimen Shop, Yasmetic, Technolife cosmetics |

Pages were picked only because they can be fetched (robots.txt allows it and the server answers from this network). Most Iran-hosted sites refuse connections from this network, so the Persian set is limited to one niche.

Page text stays in a local work folder. It is not committed, because it belongs to the sites.

## Questions (3 per page, in the page's language)
- en-invoice: best invoicing app for a small contractor or freelancer; send estimates and get paid online from a phone; easiest invoicing tool for a one-person service business.
- en-password: best free password manager; best password manager for sharing with family; an open-source password manager I can trust.
- fa-beauty-a and fa-beauty-b (the same three): best site to buy original cosmetics; where to buy authentic skincare online with an authenticity guarantee; recommend a reliable online store for skincare products.

## Conditions (4 per page, 5 runs each: 4 × 3 × 4 × 5 = 240 calls)
1. **baseline:** the page as fetched.
2. **aa:** an identical copy of the page. It measures noise only and must not WIN.
3. **answer-first:** 2–4 opening sentences answer the buyer questions directly, then the original page follows. It uses only facts on the page.
4. **structure:** the same facts reorganized under clear headings with a short list of key facts (what it is, who it's for, price or free tier, payments or guarantee), with page noise (countdowns, repeated labels) removed.

No variant may add a number, quote or claim that isn't on the page. Every item `smn variant` flags is either removed or confirmed against the page.

## Engine and rule
- Engine: `smn.py` 0.1.0 `engine_claude` (Claude Sonnet), the prompt as committed. The seed for each (question, run) pair is the same across conditions, so the comparisons are paired.
- Verdict: `smn report` exactly as committed. Two paired tests run against the baseline: exact McNemar on cited, and a sign test on quote share (|diff| > 0.01). Each uses α = 0.025.
- Failed engine calls are skipped by `smn` and counted in the write-up. There are no reruns and no dropped pages.

## What gets reported
- For each page: the baseline cited, quote and brand values, and the verdict of each condition.
- **Check 1 (false wins):** aa gives 0 WIN out of 4.
- **Check 2 (does it find anything?):** the number of WIN, WORSE and no-difference results among the 8 real variants. No target is set; "nothing wins" is an acceptable result.
- **Cost:** total cost and calls.

The full run (about 12 pages) happens only if the user approves after seeing the pilot.
