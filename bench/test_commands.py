#!/usr/bin/env python3
"""End-to-end check of every command on a throwaway folder, with the deterministic fake engine (no model calls).

  python bench/test_commands.py
"""
import subprocess, sys, tempfile
from pathlib import Path

SMN = Path(__file__).resolve().parent.parent / "skills" / "say-my-name" / "scripts" / "smn.py"


def smn(cwd, *args, ok=True):
    r = subprocess.run([sys.executable, str(SMN), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    assert (r.returncode == 0) == ok, f"{args}: exit {r.returncode}\n{r.stdout}{r.stderr}"
    return r.stdout + r.stderr


with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    page = d / "page.md"
    page.write_text("# Acme\nAcme helps businesses keep things in order. Founded in 2019.\n", encoding="utf-8")
    (d / "c1.md").write_text("The best accounting software for small shops is easy invoicing and stock tracking.", encoding="utf-8")
    (d / "c2.md").write_text("Accounting software reviews: invoicing tools compared for small business owners.", encoding="utf-8")
    (d / "c3.md").write_text("A recipe for lemon cake with fresh lemons and sugar.", encoding="utf-8")
    q1, q2 = "best accounting software for small shops", "which invoicing software is easy for small shops"
    out = smn(d, "prep", "--page", "page.md", "--brand", "Acme", "--question", q1, "--question", q2,
              "--competitor", "c1.md", "--competitor", "c2.md", "--competitor", "c3.md", "--runs", "5")
    assert "3 competitors, 2 questions x 5 runs" in out, out

    out = smn(d, "test", "--engine", "fake")  # no --yes: estimate only, nothing runs
    assert "10 engine calls" in out and not (d / ".smn/results").exists(), out
    smn(d, "test", "--engine", "fake", "--yes")

    # A/A: an identical copy must not "win"
    (d / "same.txt").write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    smn(d, "variant", "same", "--from", "same.txt")
    smn(d, "test", "same", "--engine", "fake", "--yes")
    # planted signal: a rewrite that answers the questions directly must win
    win = ("Acme is the best accounting software for small shops: easy invoicing software, stock tracking and "
           "invoices for small shops. Founded in 2019.")
    (d / "answer.txt").write_text(win, encoding="utf-8")
    out = smn(d, "variant", "answer-first", "--from", "answer.txt")
    assert "invented" not in out, out  # 2019 is on the page, nothing is new
    (d / "made-up.txt").write_text(win + " Trusted by 4,000 shops.", encoding="utf-8")
    assert "number: 4,000" in smn(d, "variant", "made-up", "--from", "made-up.txt")
    smn(d, "test", "answer-first", "--engine", "fake", "--yes")

    out = smn(d, "report")
    line = {ln.split()[0]: ln for ln in out.splitlines() if ln.startswith("  ") and ln.split()}
    assert "WIN" in line["answer-first"], out
    assert "no measurable difference" in line["same"], out
    assert "Simulated engine" in out and "Best measurable winner: answer-first" in out, out

    # apply: diff only without --yes, then write, then undo byte for byte
    before = page.read_bytes()
    out = smn(d, "apply", "answer-first")
    assert "+Acme is the best accounting software" in out and page.read_bytes() == before, out
    smn(d, "apply", "answer-first", "--yes")
    assert page.read_bytes() != before and b"best accounting software" in page.read_bytes()
    smn(d, "undo")
    assert page.read_bytes() == before
    smn(d, "undo", ok=False)  # nothing left to undo

    # undo refuses to clobber edits made after apply
    smn(d, "apply", "answer-first", "--yes")
    page.write_text(page.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
    assert "edited after apply" in smn(d, "undo", ok=False)
    smn(d, "undo", "--force")
    assert page.read_bytes() == before

    # two applies back to back (same second) keep separate backups; two undos reach the original
    smn(d, "apply", "answer-first", "--yes")
    smn(d, "apply", "made-up", "--yes")
    smn(d, "undo")
    assert b"4,000" not in page.read_bytes() and b"best accounting software" in page.read_bytes()
    smn(d, "undo")
    assert page.read_bytes() == before

    # HTML pages are never edited
    (d / "site.html").write_text("<main><p>" + "Acme software. " * 40 + "</p></main>", encoding="utf-8")
    smn(d, "prep", "--page", "site.html", "--brand", "Acme", "--question", q1, "--competitor", "c1.md", "--competitor", "c2.md")
    (d / "w.txt").write_text(win, encoding="utf-8")
    smn(d, "variant", "w", "--from", "w.txt")
    assert "only edits local .md" in smn(d, "apply", "w", "--yes", ok=False)

    # Persian page: issues are reported at prep
    (d / "fa.md").write_text("این نرم افزار حسابداري برای فروشگاه های کوچك است و کار را ساده می کند. " * 5, encoding="utf-8")
    out = smn(d, "prep", "--page", "fa.md", "--brand", "آکمه", "--question", "بهترین نرم‌افزار حسابداری؟",
              "--competitor", "c1.md", "--competitor", "c2.md")
    assert "arabic_yeh_kaf" in out and "space_instead_of_zwnj" in out, out

print("commands ok")
