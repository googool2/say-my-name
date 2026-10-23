# Rewrite strategies worth testing

These are candidates, not rules. Research disagrees about how well they work, which is the reason this skill tests them. Use one idea per variant, so a win can be explained.

| Variant idea | What to change | Source of the idea |
|---|---|---|
| **answer-first** | Open with a 1–2 sentence direct answer to the main buyer question, using the words people ask with. Details come after. | Common GEO practice; answer engines quote early, self-contained sentences |
| **statistics** | Add specific numbers, but **only real ones** the user gave or the page already has elsewhere: prices, counts, test results, dates. | Aggarwal et al., *GEO* (2023): adding statistics was among the strongest methods |
| **quotations** | Add a short attributed quote (a customer, an expert, a review), but **only real ones**. | Aggarwal et al. (2023): quotation addition improved visibility |
| **cite-sources** | Name where claims come from (a standard, a study, a certification). | Aggarwal et al. (2023) |
| **entity-clarity** | State plainly what the brand is, who it's for, where it operates and how it differs, in one paragraph. Use the brand name instead of "we". | Answer engines need to connect the page to the entity asked about |
| **structure** | Short sections with question-style headings, plus a comparison table or an FAQ. | Common GEO practice |
| **persian-normalize** (Persian pages) | Replace Arabic ي/ك with Persian ی/ک, add the missing ZWNJs (می‌, ‌ها), and use one digit style. Nothing else changes. | Inconsistent Persian characters split one word into several spellings |

## Don't
- **Keyword stuffing.** It didn't help in the GEO experiments.
- **Inventing facts, reviews or numbers.** `smn.py variant` flags new numbers and quotes for this reason.
- **Expecting a blanket win.** A 2026 study found that token-level GEO heuristics don't consistently raise citations across engines, and can hurt them. When the report says "no measurable difference", believe it.

## References
- Aggarwal, Murahari et al., *GEO: Generative Engine Optimization* (2023). https://arxiv.org/abs/2311.09735
- *Think Before Writing: Feature-Level Multi-Objective Optimization for Generative Citation Visibility* (2026). https://arxiv.org/abs/2604.19113
