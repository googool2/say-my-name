#!/usr/bin/env python3
"""Can the citation lab be trusted? Four checks on an English and a Persian fixture.

  python bench/bench.py [--engine fake|claude] [--runs 5] [WORKDIR]   -> bench/RESULTS.md, bench/results.json

1. A/A          the page against an identical copy must NOT be a win (false-win guard)
2. planted      a version that answers the buyer questions directly must WIN
3. removed      a version stripped of the useful facts must not win (and should be WORSE)
4. repeat       two baseline-like runs (baseline and the identical copy) cite the page at similar rates
With --engine claude this uses your Claude Code quota; the script prints the call count first and asks.
"""
import argparse, importlib.util, json, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SMN = HERE.parent / "skills" / "say-my-name" / "scripts" / "smn.py"
spec = importlib.util.spec_from_file_location("smn", SMN)
smn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smn)

FIXTURES = {
    "en": {
        "brand": ["Ledgerly"],
        "questions": [
            "What is the best accounting software for a small shop?",
            "Which app handles invoices and stock for a small store?",
            "Is there affordable bookkeeping software with VAT reports for small retailers?",
            "What accounting app should a two-person shop use?",
        ],
        "baseline": """# Ledgerly
Ledgerly started in 2019 when our founders, two former bakers, got tired of spreadsheets. Since then we have grown
into a team of twelve people who care about craft, community and good coffee. We believe software should feel calm.
Our product brings your numbers together in one place. Many of our customers run independent businesses and tell us
they finally understand their money. Ledgerly also includes invoices, stock counts and tax reports, and plans start
at 9 dollars a month. Read our blog for stories from the people who use it every day.""",
        "planted": """# Ledgerly: accounting software for small shops
Ledgerly is accounting software built for small shops and small stores. It handles invoices, stock and VAT reports in
one app, which makes it a good fit for a two-person shop or any small retailer.
- Invoices: create and send invoices to customers in seconds.
- Stock: track inventory for a small store, with low-stock alerts.
- VAT reports: affordable bookkeeping with ready-made VAT reports for small retailers.
- Price: plans start at 9 dollars a month.
Ledgerly started in 2019 and is run by a team of twelve people.""",
        "removed": """# Ledgerly
Ledgerly started in 2019 when our founders, two former bakers, got tired of spreadsheets. Since then we have grown
into a team of twelve people who care about craft, community and good coffee. We believe software should feel calm.
Read our blog for stories from the people who use it every day, and follow us for updates.""",
        "competitors": {
            "c1.md": """# ShopBooks
ShopBooks is accounting software for small shops. It covers invoices, inventory and sales tax in one simple app.
Small retailers use it to send invoices, count stock and file VAT. Plans start at 12 dollars a month.""",
            "c2.md": """# TimeTally
TimeTally is a bookkeeping app for freelancers and consultants. Track billable hours, send invoices to clients and
see what you earned this month. Ideal for solo designers, writers and developers.""",
            "c3.md": """# Enterprisa ERP
Enterprisa is an enterprise resource planning suite for manufacturers with more than 500 employees. Modules cover
procurement, multi-entity consolidation, payroll and supply chain planning across many countries.""",
            "c4.md": """# ChainPOS
ChainPOS is a point of sale and inventory platform for retail chains with 50 or more stores. Central buying,
store-to-store transfers and head-office dashboards keep large chains in sync.""",
        },
    },
    "fa": {
        "brand": ["حساب‌یار", "Hesabyar"],
        "questions": [
            "بهترین نرم‌افزار حسابداری برای یک مغازه کوچک چیست؟",
            "کدام نرم‌افزار فاکتور و انبار یک فروشگاه کوچک را مدیریت می‌کند؟",
            "یک نرم‌افزار حسابداری ارزان با گزارش مالیات بر ارزش افزوده برای فروشگاه کوچک می‌شناسید؟",
        ],
        # deliberately typed with Arabic ي/ك and spaces instead of ZWNJ, as many Persian pages are
        "baseline": """# حساب يار
حساب يار در سال ۱۳۹۸ توسط دو نفر شروع شد كه از اكسل خسته شده بودند. امروز تيم ما دوازده نفر است و به كيفيت و
مشتري اهميت مي دهيم. ما فكر مي كنيم نرم افزار بايد آرام باشد. بسياري از مشتريان ما كسب و كار هاي مستقل دارند.
حساب يار فاكتور، انبار و گزارش ماليات را هم دارد و قيمت از ماهانه ۲۹۰ هزار تومان شروع مي شود.""",
        "planted": """# حساب‌یار: نرم‌افزار حسابداری برای مغازه و فروشگاه کوچک
حساب‌یار نرم‌افزار حسابداری مخصوص مغازه‌ها و فروشگاه‌های کوچک است. فاکتور، انبار و گزارش مالیات بر ارزش افزوده را
در یک نرم‌افزار مدیریت می‌کند و برای یک مغازه کوچک گزینه‌ای ارزان است.
- فاکتور: صدور فاکتور برای مشتری در چند ثانیه.
- انبار: مدیریت انبار فروشگاه کوچک با هشدار کمبود کالا.
- مالیات: گزارش آماده مالیات بر ارزش افزوده.
- قیمت: از ماهانه ۲۹۰ هزار تومان.""",
        "removed": """# حساب‌یار
حساب‌یار در سال ۱۳۹۸ توسط دو نفر شروع شد که از اکسل خسته شده بودند. امروز تیم ما دوازده نفر است و به کیفیت و
مشتری اهمیت می‌دهیم. برای خواندن داستان مشتریان ما، به وبلاگ سر بزنید.""",
        "competitors": {
            "c1.md": """# دفترچه
دفترچه نرم‌افزار حسابداری برای مغازه‌های کوچک است. فاکتور، انبار و مالیات را در یک برنامه ساده مدیریت می‌کند و
قیمت آن از ماهانه ۳۵۰ هزار تومان شروع می‌شود.""",
            "c2.md": """# ساعت‌شمار
ساعت‌شمار برنامه‌ای برای فریلنسرها است: ثبت ساعت کار، صدور صورت‌حساب برای کارفرما و گزارش درآمد ماهانه.""",
            "c3.md": """# سازمان‌پلاس
سازمان‌پلاس سامانه برنامه‌ریزی منابع سازمانی برای کارخانه‌های بزرگ با بیش از ۵۰۰ کارمند است: خرید، حقوق و
دستمزد و زنجیره تأمین.""",
        },
    },
}


def run(cwd, *args, engine):
    extra = ["--engine", engine, "--yes"] if args[0] == "test" else []
    r = subprocess.run([sys.executable, str(SMN), *args, *extra], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"smn {' '.join(args)} failed:\n{r.stdout}{r.stderr}")
    return r.stdout


def bench_fixture(name, fx, work, engine, runs):
    d = work / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    (d / "page.md").write_text(fx["baseline"], encoding="utf-8")
    for fname, text in fx["competitors"].items():
        (d / fname).write_text(text, encoding="utf-8")
    args = ["prep", "--page", "page.md", "--runs", str(runs)]
    for b in fx["brand"]:
        args += ["--brand", b]
    for q in fx["questions"]:
        args += ["--question", q]
    for fname in fx["competitors"]:
        args += ["--competitor", fname]
    prep_out = run(d, *args, engine=engine)
    for variant in ("aa", "planted", "removed"):
        (d / f"{variant}.txt").write_text(fx["baseline"] if variant == "aa" else fx[variant], encoding="utf-8")
        run(d, "variant", variant, "--from", f"{variant}.txt", engine=engine)
    for t in ("baseline", "aa", "planted", "removed"):
        run(d, "test", *([] if t == "baseline" else [t]), engine=engine)
    res = {t: json.loads((d / f".smn/results/{t}.json").read_text(encoding="utf-8")) for t in ("baseline", "aa", "planted", "removed")}
    m = {t: smn.metrics(r["runs"]) for t, r in res.items()}
    c = {t: smn.compare(res["baseline"]["runs"], res[t]["runs"]) for t in ("aa", "planted", "removed")}
    checks = {
        "A/A is not a win": c["aa"]["verdict"] != "WIN",
        "planted wins": c["planted"]["verdict"] == "WIN",
        "removed does not win": c["removed"]["verdict"] != "WIN",
        "repeat within 10 points": abs(m["baseline"]["cited"] - m["aa"]["cited"]) <= 0.10,
    }
    if name == "fa":
        checks["Persian issues detected"] = "arabic_yeh_kaf" in prep_out and "space_instead_of_zwnj" in prep_out
        checks["Persian brand detected"] = m["planted"]["brand"] > 0
    calls = sum(len(r["runs"]) for r in res.values())
    cost = sum(x["cost_usd"] for r in res.values() for x in r["runs"])
    return {"metrics": m, "compare": c, "checks": checks, "calls": calls, "cost_usd": round(cost, 3),
            "seconds": round(sum(r["seconds"] for r in res.values()), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir", nargs="?", default=str(HERE / "_work"))
    ap.add_argument("--engine", choices=["fake", "claude"], default="fake")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--yes", action="store_true", help="skip the confirmation for --engine claude")
    a = ap.parse_args()
    calls = sum(len(fx["questions"]) * a.runs * 4 for fx in FIXTURES.values())
    if a.engine == "claude" and not a.yes:
        print(f"This makes {calls} Claude calls (about ${0.05 * calls:.0f}-{0.08 * calls:.0f} of quota). Rerun with --yes.")
        return
    work = Path(a.workdir).resolve()
    out = {"engine": a.engine, "runs": a.runs, "date": time.strftime("%Y-%m-%d"), "fixtures": {}}
    for name, fx in FIXTURES.items():
        print(f"== {name}", flush=True)
        out["fixtures"][name] = bench_fixture(name, fx, work, a.engine, a.runs)
    ok = all(v for f in out["fixtures"].values() for v in f["checks"].values())
    out["all_passed"] = ok
    (HERE / ("results.json" if a.engine == "claude" else "results-fake.json")).write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [f"# Say My Name: lab self-test ({a.engine} engine)", "",
             f"{a.runs} runs per question, {out['date']}. Variants: an identical copy (A/A), a version that answers the "
             "buyer questions directly (planted), and one stripped of the useful facts (removed).", ""]
    for name, f in out["fixtures"].items():
        lines += [f"## {'English' if name == 'en' else 'Persian'} fixture", "",
                  "| version | cited | quote share | brand | verdict vs baseline |", "|---|---:|---:|---:|---|"]
        for t in ("baseline", "aa", "planted", "removed"):
            mm = f["metrics"][t]
            v = "-" if t == "baseline" else f"{f['compare'][t]['verdict']} (p={f['compare'][t]['p']:.3f})"
            lines.append(f"| {t} | {mm['cited']:.0%} | {mm['quote']:.2f} | {mm['brand']:.0%} | {v} |")
        lines += ["", "| check | result |", "|---|---|"]
        lines += [f"| {k} | {'✅' if v else '❌'} |" for k, v in f["checks"].items()]
        lines += ["", f"{f['calls']} calls, ${f['cost_usd']:.2f}, {f['seconds']:.0f} s.", ""]
    (HERE / ("RESULTS.md" if a.engine == "claude" else "RESULTS-fake.md")).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
