# Say My Name: lab self-test (fake engine)

5 runs per question, 2026-10-23. Variants: an identical copy (A/A), a version that answers the buyer questions directly (planted), and one stripped of the useful facts (removed).

## English fixture

| version | cited | quote share | brand | verdict vs baseline |
|---|---:|---:|---:|---|
| baseline | 60% | 0.26 | 15% | - |
| aa | 60% | 0.26 | 15% | no measurable difference (citation p=1.000, quote p=1.000) |
| planted | 100% | 0.62 | 100% | WIN (citation p=0.008, quote p=0.000) |
| removed | 35% | 0.17 | 15% | no measurable difference (citation p=0.062, quote p=0.062) |

| check | result |
|---|---|
| A/A is not a win | ✅ |
| planted wins | ✅ |
| removed does not win | ✅ |
| repeat within 10 points | ✅ |

80 calls, $0.00, 0 s.

## Persian fixture

| version | cited | quote share | brand | verdict vs baseline |
|---|---:|---:|---:|---|
| baseline | 40% | 0.15 | 0% | - |
| aa | 40% | 0.15 | 0% | no measurable difference (citation p=1.000, quote p=1.000) |
| planted | 100% | 0.62 | 100% | WIN (citation p=0.004, quote p=0.000) |
| removed | 13% | 0.05 | 0% | no measurable difference (citation p=0.219, quote p=0.219) |

| check | result |
|---|---|
| A/A is not a win | ✅ |
| planted wins | ✅ |
| removed does not win | ✅ |
| repeat within 10 points | ✅ |
| Persian issues detected | ✅ |
| Persian brand detected | ✅ |

60 calls, $0.00, 0 s.
