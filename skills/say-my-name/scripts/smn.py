#!/usr/bin/env python3
"""Say My Name: test whether an AI answer engine would cite your page, and keep only rewrites that win.

  smn.py prep --page FILE_OR_URL --brand NAME [--brand ...] --question Q [--question ...]
              --competitor FILE_OR_URL [--competitor ...] [--runs 5] [--facts FILE]
  smn.py variant NAME --from FILE        store a rewrite; flags numbers and quotes not in your page or facts
  smn.py test [NAME] [--yes]             without --yes: print the estimate only. NAME defaults to baseline
  smn.py report                          compare every tested variant with the baseline
  smn.py apply NAME [--yes]              without --yes: show the diff only. Local .md/.txt/.mdx pages only
  smn.py undo                            restore the page as it was before the last apply

State lives in ./.smn/ . Stdlib only. Engines: claude (headless Claude Code, default) or fake (tests).
"""
import argparse, datetime, difflib, hashlib, json, math, os, random, re, shutil, subprocess, sys, tempfile, time
import urllib.parse, urllib.request, urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path

__version__ = "0.1.0"
STATE = Path(".smn")
UA = "SayMyName/0.1 (+https://github.com/googool2/say-my-name)"
MAX_WORDS = 1500  # per source; long pages are cut the same way for every variant
EDITABLE = {".md", ".mdx", ".txt", ".markdown"}
NO_TOOLS = ["Bash", "Edit", "Write", "Read", "Glob", "Grep", "WebFetch", "WebSearch", "Task", "Agent", "NotebookEdit"]
HONESTY = ("Simulated engine: this measures how likely your page is to be cited and quoted when it is among the "
           "sources, not whether a live AI search retrieves it in the first place.")

# ---------------------------------------------------------------- text
PERSIAN = re.compile(r"[پچژگیکۀ]")
ARABIC_YEH_KAF = re.compile(r"[يك]")
ZWNJ_MI = re.compile(r"(?<![\w‌])(ن?می) (?=[؀-ۿ])")          # "می رود" -> "می‌رود"
ZWNJ_HA = re.compile(r"(?<=[؀-ۿ]) (ها|های|هایی|ترین|تر)(?![؀-ۿ])")
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize(s):
    """For matching only (brand names, numbers): Persian letters, Western digits, no ZWNJ, casefolded."""
    return s.translate(DIGITS).replace("ي", "ی").replace("ك", "ک").replace("‌", "").casefold()


def persian_issues(text):
    """Counts of common Persian typing problems, or {} for non-Persian text."""
    if len(PERSIAN.findall(text)) < 20:
        return {}
    issues = {"arabic_yeh_kaf": len(ARABIC_YEH_KAF.findall(text)),
              "space_instead_of_zwnj": len(ZWNJ_MI.findall(text)) + len(ZWNJ_HA.findall(text)),
              "mixed_digits": int(bool(re.search(r"[0-9]", text)) + bool(re.search(r"[۰-۹]", text)) + bool(re.search(r"[٠-٩]", text)) > 1)}
    return {k: v for k, v in issues.items() if v}


class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip, self.main_depth, self.main = [], 0, 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag in ("main", "article"):
            self.main_depth += 1
        if tag in ("p", "br", "li", "h1", "h2", "h3", "h4", "tr", "div", "section"):
            self._emit("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in ("main", "article") and self.main_depth:
            self.main_depth -= 1

    def handle_data(self, data):
        if not self.skip:
            self._emit(data)

    def _emit(self, s):
        self.parts.append(s)
        if self.main_depth:
            self.main.append(s)


def html_to_text(html):
    p = _Text()
    p.feed(html)
    body = "".join(p.main) if len(" ".join(p.main).split()) > 80 else "".join(p.parts)  # prefer <main>/<article>
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in body.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def fetch(src):
    """(text, kind) from a local file or a URL. URLs honor robots.txt and wait a second."""
    if not re.match(r"https?://", src):
        p = Path(src)
        raw = p.read_text(encoding="utf-8", errors="replace")
        return (html_to_text(raw) if p.suffix.lower() in (".html", ".htm") else raw.strip()), "file"
    parts = urllib.parse.urlsplit(src)
    rp = urllib.robotparser.RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        rp.read()
        if not rp.can_fetch(UA, src):
            sys.exit(f"robots.txt disallows fetching {src}; save the page as a file and pass the file instead")
    except Exception:
        pass  # no robots.txt reachable: proceed politely
    time.sleep(1)
    req = urllib.request.Request(src, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return html_to_text(r.read().decode(charset, errors="replace")), "url"


def clip(text, n=MAX_WORDS):
    words = text.split()
    return text if len(words) <= n else " ".join(words[:n]) + " …"


NUM = re.compile(r"\d[\d,.٫٬٬٫]*%?")
QUOTE = re.compile(r"[\"“«]([^\"”»]{12,200})[\"”»]")


def unsupported_facts(variant, known):
    """Numbers and quoted passages in a rewrite that appear nowhere in the page or the facts file."""
    known_n = normalize(known)
    nums = {n.strip(".,") for n in NUM.findall(normalize(variant))}
    new_nums = sorted(n for n in nums if n and n not in known_n)
    new_quotes = [q for q in QUOTE.findall(variant) if normalize(q) not in known_n]
    return new_nums, new_quotes


# ---------------------------------------------------------------- one engine run
def build_prompt(question, sources):
    blocks = "\n\n".join(f"[S{i}]\n{text}" for i, text in enumerate(sources, 1))
    return ("You are an answer engine. Answer the question using only the sources below. Cite every claim inline "
            "with the id of the source it comes from, like [S2]. Cite only sources you actually used. Answer in the "
            "language of the question, in at most 150 words.\n\n"
            f"SOURCES\n\n{blocks}\n\nQUESTION\n{question}\n")


CITE = re.compile(r"\[S(\d+)\]")


def score(answer, ours, brands):
    """cited, first position among distinct citations, position-weighted quote share, brand mentioned."""
    order = list(dict.fromkeys(int(n) for n in CITE.findall(answer)))
    sentences = []
    for s in (s for s in re.split(r"(?<=[.!?؟])\s+|\n+", answer) if s.strip()):
        if sentences and not CITE.sub("", s).strip(" .,;:"):  # "Claim. [S2]": the citation belongs to the claim before it
            sentences[-1] += " " + s
        else:
            sentences.append(s)
    total = mine = 0.0
    for i, s in enumerate(sentences):
        ids = set(int(n) for n in CITE.findall(s))
        if not ids:
            continue
        w = len(CITE.sub("", s).split()) * math.exp(-i / max(len(sentences), 1))  # GEO paper: earlier text counts more
        total += w
        if ours in ids:
            mine += w / len(ids)
    text = normalize(CITE.sub("", answer))
    return {"cited": ours in order, "position": order.index(ours) + 1 if ours in order else None,
            "quote_share": round(mine / total, 4) if total else 0.0,
            "brand": any(normalize(b) in text for b in brands)}


def engine_fake(question, sources, rnd):
    """Deterministic stand-in for tests: cites the two sources sharing most words with the question."""
    q = set(re.findall(r"\w+", normalize(question)))
    ranked = sorted(range(len(sources)), key=lambda i: (-len(q & set(re.findall(r"\w+", normalize(sources[i])))), rnd.random()))
    a, b = ranked[0] + 1, ranked[1] + 1
    lead = " ".join(sources[a - 1].split()[:6])
    return f"{lead} [S{a}]. More detail is in another source [S{b}].", {"tokens": 0, "cost_usd": 0.0}


def engine_claude(prompt, model):
    claude = shutil.which("claude")
    if not claude:
        sys.exit("the claude CLI is not on PATH; install Claude Code or use --engine fake")
    # inherited CLAUDE* variables from a parent session would hijack auth and settings
    env = {k: v for k, v in os.environ.items() if not (k.startswith("CLAUDE") or k == "ANTHROPIC_BASE_URL")}
    with tempfile.TemporaryDirectory() as empty:  # no project CLAUDE.md can leak into the answer
        r = subprocess.run([claude, "-p", "--output-format", "json", "--model", model, "--setting-sources", "project",
                            "--strict-mcp-config", "--no-session-persistence", "--disallowedTools", *NO_TOOLS],
                           input=prompt, cwd=empty, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise RuntimeError((r.stdout + r.stderr)[-300:])
    if out.get("is_error"):
        raise RuntimeError(out.get("result") or "engine error")
    u = out.get("usage", {})
    tokens = sum(u.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
    return out.get("result") or "", {"tokens": tokens, "cost_usd": out.get("total_cost_usd") or 0.0}


# ---------------------------------------------------------------- state
def load():
    if not (STATE / "config.json").exists():
        sys.exit("nothing prepared yet: run `smn.py prep ...` first")
    return json.loads((STATE / "config.json").read_text(encoding="utf-8"))


def save(cfg):
    (STATE / "config.json").write_text(json.dumps(cfg, indent=1, ensure_ascii=False), encoding="utf-8")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def page_text(cfg, name):
    p = STATE / ("page.txt" if name == "baseline" else f"variants/{name}.txt")
    if not p.exists():
        sys.exit(f"no variant named {name!r}")
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------- commands
def cmd_prep(a):
    STATE.mkdir(exist_ok=True)
    (STATE / "comp").mkdir(exist_ok=True)
    (STATE / "variants").mkdir(exist_ok=True)
    text, kind = fetch(a.page)
    (STATE / "page.txt").write_text(text, encoding="utf-8")
    comps = []
    for i, c in enumerate(a.competitor, 1):
        ct, _ = fetch(c)
        (STATE / f"comp/C{i}.txt").write_text(ct, encoding="utf-8")
        comps.append({"id": f"C{i}", "source": c, "words": len(ct.split())})
    facts = Path(a.facts).read_text(encoding="utf-8") if a.facts else ""
    cfg = {"version": __version__, "page": a.page, "kind": kind, "brands": a.brand, "questions": a.question,
           "competitors": comps, "runs": a.runs, "facts": facts, "created": datetime.datetime.now().isoformat(timespec="seconds")}
    if kind == "file":
        cfg["page_sha"] = sha(Path(a.page).read_bytes())
    save(cfg)
    words = len(text.split())
    print(f"Say My Name {__version__}: page {words:,} words ({'clipped to ' + str(MAX_WORDS) if words > MAX_WORDS else 'full'}), "
          f"{len(comps)} competitors, {len(a.question)} questions x {a.runs} runs.")
    for c in comps:
        print(f"  {c['id']}  {c['words']:>6,} words  {c['source']}")
    issues = persian_issues(text)
    if issues:
        print("Persian text issues on your page (fixing them is a candidate rewrite):")
        for k, v in issues.items():
            print(f"  {k}: {v}")
    if len(comps) < 2:
        print("Warning: with fewer than 2 competitors almost any page gets cited; add more for a meaningful test.")
    print(f"Next: smn.py test   (shows the cost estimate; nothing runs without --yes)")


def estimate(cfg, n_variants=1):
    calls = len(cfg["questions"]) * cfg["runs"] * n_variants
    src_words = min(len(page_text(cfg, "baseline").split()), MAX_WORDS) + sum(min(c["words"], MAX_WORDS) for c in cfg["competitors"])
    prompt_tokens = int(src_words * 1.6) + 300  # ~1.3 tokens/word in English, more in Persian
    return calls, prompt_tokens


def cmd_test(a):
    cfg = load()
    name = a.name or "baseline"
    ours = page_text(cfg, name)
    comps = [(STATE / f"comp/{c['id']}.txt").read_text(encoding="utf-8") for c in cfg["competitors"]]
    calls, prompt_tokens = estimate(cfg)
    if not a.yes:
        hist = [r for f in (STATE / "results").glob("*.json") for r in json.loads(f.read_text(encoding="utf-8"))["runs"]
                if r.get("cost_usd")] if (STATE / "results").exists() else []
        per_call = sum(r["cost_usd"] for r in hist) / len(hist) if hist else None
        guess = f"measured ${per_call:.3f}/call so far -> about ${per_call * calls:.2f}" if per_call else \
            "roughly $0.03-0.08 per call with Claude Sonnet -> about ${:.2f}-{:.2f}".format(0.03 * calls, 0.08 * calls)
        print(f"Testing {name!r}: {calls} engine calls ({len(cfg['questions'])} questions x {cfg['runs']} runs), "
              f"~{prompt_tokens:,} prompt tokens each; {guess}. This uses your Claude Code quota.")
        print(f"Run it with: smn.py test {name} --yes")
        return
    runs, t0 = [], time.time()
    for qi, q in enumerate(cfg["questions"]):
        for r in range(cfg["runs"]):
            seed = int(sha(f"{q}|{r}".encode())[:12], 16)  # same seed for every variant -> paired comparison
            rnd = random.Random(seed)
            order = list(range(len(comps) + 1))
            rnd.shuffle(order)
            sources = [clip(ours) if i == 0 else clip(comps[i - 1]) for i in order]
            our_id = order.index(0) + 1
            try:
                if a.engine == "fake":
                    answer, use = engine_fake(q, sources, random.Random(seed))
                else:
                    answer, use = engine_claude(build_prompt(q, sources), a.model)
            except RuntimeError as e:
                print(f"  q{qi + 1} run {r + 1}: engine error, skipped ({e})")
                continue
            res = {"q": qi, "run": r, "seed": seed, "our_id": our_id, **score(answer, our_id, cfg["brands"]), **use,
                   "answer": answer}
            runs.append(res)
            print(f"  q{qi + 1} run {r + 1}: {'cited' if res['cited'] else '-'}"
                  f"{'' if res['position'] is None else ' #' + str(res['position'])} quote {res['quote_share']:.2f}"
                  f"{' brand' if res['brand'] else ''}", flush=True)
    (STATE / "results").mkdir(exist_ok=True)
    (STATE / f"results/{name}.json").write_text(json.dumps(
        {"name": name, "engine": a.engine, "model": a.model, "page_sha": sha(ours.encode()), "runs": runs,
         "seconds": round(time.time() - t0, 1)}, indent=1, ensure_ascii=False), encoding="utf-8")
    m = metrics(runs)
    print(f"{name}: cited {m['cited']:.0%}, quote share {m['quote']:.2f}, brand {m['brand']:.0%} "
          f"({len(runs)} runs, ${sum(r['cost_usd'] for r in runs):.2f}). Next: smn.py report")


def metrics(runs):
    n = max(len(runs), 1)
    pos = [r["position"] for r in runs if r["position"]]
    return {"cited": sum(r["cited"] for r in runs) / n, "quote": sum(r["quote_share"] for r in runs) / n,
            "brand": sum(r["brand"] for r in runs) / n, "position": sum(pos) / len(pos) if pos else None, "n": len(runs)}


def mcnemar_p(b, c):
    """Exact two-sided p for paired yes/no outcomes: b = only baseline cited, c = only variant cited."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def compare(base, var):
    """Pair runs by (question, run) and decide whether the variant measurably wins."""
    bmap = {(r["q"], r["run"]): r for r in base}
    pairs = [(bmap[(r["q"], r["run"])], r) for r in var if (r["q"], r["run"]) in bmap]
    b = sum(1 for x, y in pairs if x["cited"] and not y["cited"])
    c = sum(1 for x, y in pairs if y["cited"] and not x["cited"])
    p = mcnemar_p(b, c)
    dq = sum(y["quote_share"] - x["quote_share"] for x, y in pairs) / max(len(pairs), 1)
    win = c > b and p < 0.05 and dq >= -0.02
    lose = b > c and p < 0.05
    return {"pairs": len(pairs), "only_baseline": b, "only_variant": c, "p": p, "quote_delta": dq,
            "verdict": "WIN" if win else ("WORSE" if lose else "no measurable difference")}


def cmd_report(a):
    cfg = load()
    res = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((STATE / "results").glob("*.json"))} \
        if (STATE / "results").exists() else {}
    if "baseline" not in res:
        sys.exit("test the baseline first: smn.py test --yes")
    base = res["baseline"]["runs"]
    mb = metrics(base)
    print(f"Say My Name report: {len(cfg['questions'])} questions x {cfg['runs']} runs, {len(cfg['competitors'])} competitors, "
          f"engine {res['baseline']['engine']}/{res['baseline']['model']}")
    print(f"  {'version':<16}{'cited':>7}{'quote':>8}{'brand':>7}{'avg #':>7}   verdict")
    print(f"  {'baseline':<16}{mb['cited']:>7.0%}{mb['quote']:>8.2f}{mb['brand']:>7.0%}"
          f"{(mb['position'] or 0):>7.1f}   -")
    winners = []
    for name, r in res.items():
        if name == "baseline":
            continue
        if r["engine"] != res["baseline"]["engine"] or r["model"] != res["baseline"]["model"]:
            print(f"  {name:<16} tested with a different engine/model; retest it to compare")
            continue
        m, c = metrics(r["runs"]), compare(base, r["runs"])
        print(f"  {name:<16}{m['cited']:>7.0%}{m['quote']:>8.2f}{m['brand']:>7.0%}{(m['position'] or 0):>7.1f}   "
              f"{c['verdict']} (p={c['p']:.3f}, {c['only_variant']} vs {c['only_baseline']} discordant pairs)")
        if c["verdict"] == "WIN":
            winners.append((m["cited"], name))
    print(f"Note: {HONESTY}")
    if winners:
        best = max(winners)[1]
        print(f"Best measurable winner: {best}. Apply with: smn.py apply {best}")
    else:
        print("No variant measurably beat your page. Keep your page as it is.")


def cmd_variant(a):
    cfg = load()
    text = Path(getattr(a, "from")).read_text(encoding="utf-8").strip()
    (STATE / f"variants/{a.name}.txt").write_text(text, encoding="utf-8")
    nums, quotes = unsupported_facts(text, page_text(cfg, "baseline") + "\n" + cfg.get("facts", ""))
    print(f"Stored variant {a.name!r} ({len(text.split()):,} words).")
    if nums or quotes:
        print("Check before testing: these are not in your page or facts file, so the rewrite may have invented them:")
        for n in nums:
            print(f"  number: {n}")
        for q in quotes:
            print(f"  quote: {q[:80]}")
    issues = persian_issues(text)
    if issues:
        print("Persian text issues in this variant: " + ", ".join(f"{k} {v}" for k, v in issues.items()))
    print(f"Next: smn.py test {a.name}")


def cmd_apply(a):
    cfg = load()
    page = Path(cfg["page"])
    if cfg["kind"] != "file" or page.suffix.lower() not in EDITABLE:
        sys.exit("apply only edits local .md/.mdx/.txt pages; publish the winning text yourself "
                 f"(it's in {STATE / 'variants' / (a.name + '.txt')})")
    if sha(page.read_bytes()) != cfg["page_sha"]:
        sys.exit(f"{page} changed since prep; run prep again so the test matches the file")
    new = page_text(cfg, a.name)
    diff = list(difflib.unified_diff(page.read_text(encoding="utf-8").splitlines(), new.splitlines(),
                                     str(page), f"{page} ({a.name})", lineterm=""))
    print("\n".join(diff[:200]) + ("\n... (diff truncated)" if len(diff) > 200 else ""))
    if not a.yes:
        print(f"Nothing changed. Write it with: smn.py apply {a.name} --yes")
        return
    (STATE / "backup").mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    while any((STATE / "backup").glob(stamp + ".*")):  # never overwrite a backup, even within one microsecond
        stamp += "x"
    original = page.read_bytes()
    (STATE / f"backup/{stamp}.bak").write_bytes(original)
    data = (new + ("\n" if original.endswith(b"\n") else "")).encode("utf-8")
    page.write_bytes(data)
    (STATE / f"backup/{stamp}.json").write_text(json.dumps({"page": str(page), "before": sha(original), "after": sha(data),
                                                            "variant": a.name}), encoding="utf-8")
    cfg["page_sha"] = sha(data)
    save(cfg)
    print(f"Wrote {a.name} into {page}. Backup kept; restore with: smn.py undo")


def cmd_undo(a):
    cfg = load()
    logs = sorted((STATE / "backup").glob("*.json")) if (STATE / "backup").exists() else []
    if not logs:
        sys.exit("nothing to undo")
    log = json.loads(logs[-1].read_text(encoding="utf-8"))
    page = Path(log["page"])
    if sha(page.read_bytes()) != log["after"] and not a.force:
        sys.exit(f"{page} was edited after apply; undo would overwrite those edits (use --force to do it anyway)")
    original = logs[-1].with_suffix(".bak").read_bytes()
    page.write_bytes(original)
    cfg["page_sha"] = sha(original)
    save(cfg)
    logs[-1].rename(logs[-1].with_name(logs[-1].name + ".undone"))
    print(f"Restored {page} byte for byte (variant {log['variant']} removed).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"Say My Name {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("--page", required=True)
    p.add_argument("--brand", action="append", required=True, help="every spelling, e.g. --brand Acme --brand آکمه")
    p.add_argument("--question", action="append", required=True)
    p.add_argument("--competitor", action="append", required=True)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--facts", help="file with facts a rewrite may use (numbers, quotes)")
    p = sub.add_parser("variant")
    p.add_argument("name")
    p.add_argument("--from", required=True)
    p = sub.add_parser("test")
    p.add_argument("name", nargs="?")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--engine", choices=["claude", "fake"], default="claude")
    p.add_argument("--model", default="sonnet")
    sub.add_parser("report")
    p = sub.add_parser("apply")
    p.add_argument("name")
    p.add_argument("--yes", action="store_true")
    p = sub.add_parser("undo")
    p.add_argument("--force", action="store_true")
    a = ap.parse_args()
    {"prep": cmd_prep, "variant": cmd_variant, "test": cmd_test, "report": cmd_report,
     "apply": cmd_apply, "undo": cmd_undo}[a.cmd](a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
