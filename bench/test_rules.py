#!/usr/bin/env python3
"""Fast checks for the scoring and text rules. No network, no model calls.

  python bench/test_rules.py
"""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "smn", Path(__file__).resolve().parent.parent / "skills" / "say-my-name" / "scripts" / "smn.py")
smn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smn)

# Persian normalization: Arabic letters, digits and ZWNJ don't split one word into several spellings.
assert smn.normalize("كتاب‌ها ۱۲ ٣") == smn.normalize("کتابها 12 3") == "کتابها 12 3"

# Persian issues are reported for Persian text only.
fa = "این نرم افزار حسابداري برای فروشگاه های کوچك است و کار را ساده می کند. " * 4
issues = smn.persian_issues(fa)
assert issues["arabic_yeh_kaf"] >= 8 and issues["space_instead_of_zwnj"] >= 8, issues
assert smn.persian_issues("Plain English text about accounting software. " * 10) == {}
# a page typed entirely on an Arabic keyboard is still Persian (it has گ/پ), and its problems are found
arabic_typed = "حساب يار نرم افزار حسابداري براي فروشگاه كوچك است و كار را ساده مي كند. " * 3
issues = smn.persian_issues(arabic_typed)
assert issues.get("arabic_yeh_kaf", 0) >= 20 and issues.get("space_instead_of_zwnj", 0) >= 3, issues
assert smn.persian_issues("هذا نص عربي عن برامج المحاسبة للمتاجر الصغيرة " * 4) == {}  # Arabic is left alone

# HTML: main/article content wins over navigation and scripts.
html = ("<html><nav>Home About Pricing</nav><script>var x=1</script><main><h1>Best tool</h1>"
        + "<p>" + "Useful sentence about the product. " * 30 + "</p></main><footer>Copyright</footer></html>")
text = smn.html_to_text(html)
assert "Best tool" in text and "Home About" not in text and "var x" not in text and "Copyright" not in text

# Scoring: citations, position, quote share, brand (Latin and Persian spellings).
s = smn.score("Acme is the best pick for small shops [S3]. Others exist [S1].", 3, ["Acme"])
assert s["cited"] and s["position"] == 1 and s["quote_share"] > 0.5 and s["brand"], s
s = smn.score("Most shops use a spreadsheet. [S2]", 2, ["آکمه"])  # citation after the period still counts
assert s["cited"] and s["quote_share"] == 1.0 and not s["brand"], s
s = smn.score("بهترین گزینه آكمه است [S1]. گزینه دیگر هم هست [S2].", 1, ["آکمه"])
assert s["brand"] and s["position"] == 1, s
assert not smn.score("No sources used.", 1, ["Acme"])["cited"]
# brand spelling variants: space, ZWNJ or nothing between the parts, Arabic or Persian letters
for written in ("حساب يار", "حساب‌یار", "حسابیار"):
    assert smn.score(f"{written} مناسب است [S1].", 1, ["حساب‌یار"])["brand"], written

# Paired significance: exact McNemar.
assert smn.mcnemar_p(0, 0) == 1.0
assert abs(smn.mcnemar_p(0, 6) - 0.03125) < 1e-9
assert abs(smn.mcnemar_p(1, 5) - 0.21875) < 1e-9


def runs(cited, quote=None):
    return [{"q": 0, "run": i, "cited": c, "quote_share": (quote[i] if quote else (0.3 if c else 0.0))}
            for i, c in enumerate(cited)]


assert smn.compare(runs([0] * 10), runs([1] * 10))["verdict"] == "WIN"
assert smn.compare(runs([1] * 10), runs([0] * 10))["verdict"] == "WORSE"
assert smn.compare(runs([0, 1] * 5), runs([0, 1] * 5))["verdict"] == "no measurable difference"  # A/A
assert smn.compare(runs([0] * 10), runs([1, 1, 0, 0, 0, 0, 0, 0, 0, 0]))["verdict"] == "no measurable difference"
# ceiling: cited every time in both, but the variant supplies much more of each answer -> still a WIN
assert smn.compare(runs([1] * 10, [0.25] * 10), runs([1] * 10, [0.6] * 10))["verdict"] == "WIN"
# and the opposite: same citations, much less of the answer -> WORSE
assert smn.compare(runs([1] * 10, [0.6] * 10), runs([1] * 10, [0.25] * 10))["verdict"] == "WORSE"
# A/A with noisy quote shares must not win
import random
rnd = random.Random(7)
noisy = [round(rnd.uniform(0.1, 0.5), 2) for _ in range(20)]
assert smn.compare(runs([1] * 20, noisy), runs([1] * 20, noisy[::-1]))["verdict"] != "WIN"

# Rewrites may not invent numbers or quotes.
nums, quotes = smn.unsupported_facts('Trusted by 4,000 shops since 2019. "Best tool we ever used, honestly."',
                                     "Founded in 2019. Used by shops across the country.")
assert nums == ["4,000"] and len(quotes) == 1, (nums, quotes)
assert smn.unsupported_facts("Since ۲۰۱۹.", "Founded in 2019.") == ([], [])

# Prompt and clipping.
p = smn.build_prompt("best tool?", ["alpha", "beta"])
assert "[S1]\nalpha" in p and "[S2]\nbeta" in p and "QUESTION\nbest tool?" in p
assert smn.clip("w " * 2000).split()[-1] == "…" and len(smn.clip("w " * 2000).split()) == smn.MAX_WORDS + 1

print("rules ok")
