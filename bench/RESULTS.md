# Say My Name: lab self-test (claude engine)

5 runs per question, 2026-10-23. Variants: an identical copy (A/A), a version that answers the buyer questions directly (planted), and one stripped of the useful facts (removed).

## English fixture

| version | cited | quote share | brand | verdict vs baseline |
|---|---:|---:|---:|---|
| baseline | 90% | 0.26 | 90% | - |
| aa | 85% | 0.29 | 85% | no measurable difference (citation p=1.000, quote p=0.629) |
| planted | 100% | 0.57 | 100% | WIN (citation p=0.500, quote p=0.000) |
| removed | 25% | 0.04 | 20% | WORSE (citation p=0.000, quote p=0.000) |

| check | result |
|---|---|
| A/A is not a win | ✅ |
| planted wins | ✅ |
| removed does not win | ✅ |
| repeat within 10 points | ✅ |

80 calls, $4.80, 628 s.

## Persian fixture

| version | cited | quote share | brand | verdict vs baseline |
|---|---:|---:|---:|---|
| baseline | 87% | 0.42 | 87% | - |
| aa | 93% | 0.41 | 93% | no measurable difference (citation p=1.000, quote p=0.424) |
| planted | 100% | 0.64 | 100% | WIN (citation p=0.500, quote p=0.000) |
| removed | 20% | 0.03 | 20% | WORSE (citation p=0.002, quote p=0.000) |

| check | result |
|---|---|
| A/A is not a win | ✅ |
| planted wins | ✅ |
| removed does not win | ✅ |
| repeat within 10 points | ✅ |
| Persian issues detected | ✅ |
| Persian brand detected | ✅ |

60 calls, $3.66, 636 s.
