#!/usr/bin/env python3
"""502ds.dev — the public face of 502 Design Studio's apps, built as static pages.

The legal pages are not written here. Their text has one owner, each app's own store documents
(Meridiem/docs/appstore/*.md); this script turns them into pages, so a policy changed for a release
is the policy published. On the way it drops what is not for the public:

- the draft notes (a blockquote that opens with **Draft**) and HTML comments;
- what is held for a later release (a blockquote that opens with **Held**).

Fields still in brackets (``[legal name]``) are filled from the publishing data kept outside every
repository (~/Code/Repositories/Documentation). A page with a field still empty is left out of a build
for publishing — the rest is published without it; ``--draft`` builds it anyway, marked as a draft and kept
out of search engines.

    python build.py            # build docs/ for publishing; pages with an empty field are left out
    python build.py --draft    # build docs/ with the gaps visible, to review
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
REPOS = ROOT.parent
OUT = ROOT / "docs"   # GitHub Pages serves a branch's /docs folder
DATA = REPOS / "Documentation" / "Meridiem_publicacion.txt"
DOMAIN = "502ds.dev"

# Each published page: its path on the site and the store document it comes from.
PAGES = {
    "meridiem/privacy": REPOS / "Meridiem/docs/appstore/privacy-policy.md",
    "meridiem/support": REPOS / "Meridiem/docs/appstore/support.md",
    "meridiem/terms": REPOS / "Meridiem/docs/appstore/terms-of-use.md",
    "syncthesis/privacy": REPOS / "syncThesis/docs/legal/privacy-policy.md",
}

# A bracketed field, and the label of the line in the publishing data that fills it.
FIELDS = {
    "[legal name]": "Nombre legal del titular",
    "[syncThesis.IO privacy URL]": "URL de privacidad de syncThesis.IO",
}


def publishing_data() -> dict[str, str]:
    """The value after each label's closing colon, on the label's last line; empty when not filled."""
    if not DATA.exists():
        return {}
    text = DATA.read_text(encoding="utf-8")
    found = {}
    for field, label in FIELDS.items():
        m = re.search(re.escape(label) + r"[^\n]*(?:\n[ \t]+[^\n]*)*?:[ \t]*([^\n]*)", text)
        value = m.group(1).strip() if m else ""
        if value:
            found[field] = value
    return found


def public_text(md: str) -> str:
    """The document without its draft notes, held sections and comments."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    blocks = re.split(r"\n{2,}", md)
    kept = [b for b in blocks if not re.match(r">\s*\*\*(Draft|Held)", b.lstrip())]
    # A held section can run over several blockquote paragraphs: drop the quoted run that follows a Held heading.
    out, skipping = [], False
    for b in blocks:
        head = b.lstrip()
        if re.match(r">\s*\*\*Held", head):
            skipping = True
            continue
        if skipping and head.startswith(">"):
            continue
        skipping = False
        if b in kept:
            out.append(b)
    return "\n\n".join(out).strip() + "\n"


def gaps(md: str) -> list[str]:
    """Bracketed fields left: a bracket that is not a link's text."""
    return sorted(set(re.findall(r"\[[^\]\n]+\](?!\()", md)))


CSS = """
:root{--bg:#F4FCFE;--card:#FFFFFF;--ink:#1A1A2E;--muted:#5F5F71;--faint:#71718A;--accent:#12B5C2;--accent-ink:#0A7E8A;
--soft:#E1F6F8;--line:#D5ECEF}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0C3242;--card:#11313C;--ink:#DCEEF1;
--muted:#8FB6BE;--faint:#799BA3;--accent:#5BD3DE;--accent-ink:#5BD3DE;--soft:#1B4450;--line:#1F4A56}}
:root[data-theme="dark"]{--bg:#0C3242;--card:#11313C;--ink:#DCEEF1;--muted:#8FB6BE;--faint:#799BA3;--accent:#5BD3DE;
--accent-ink:#5BD3DE;--soft:#1B4450;--line:#1F4A56}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"SF Pro Text",
"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
main{max-width:720px;margin:0 auto;padding:32px 16px 64px}
header.site{max-width:720px;margin:0 auto;padding:20px 16px 0;display:flex;gap:12px;align-items:baseline;
justify-content:space-between;flex-wrap:wrap}
header.site a{color:var(--muted);text-decoration:none;font-size:14px}
header.site a.brand{color:var(--ink);font-weight:600;font-size:15px}
nav a+a{margin-left:16px}
h1{font-size:30px;line-height:1.2;margin:8px 0 8px;letter-spacing:-.01em}
h2{font-size:20px;margin:36px 0 8px}
h3{font-size:17px;margin:24px 0 6px}
p,li{color:var(--ink)}
a{color:var(--accent-ink)}
strong{font-weight:600}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:15px;display:block;overflow-x:auto}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600}
blockquote{margin:16px 0;padding:12px 16px;background:var(--soft);border-radius:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 20px;margin:16px 0}
.card h2{margin-top:0}
.lede{color:var(--muted);font-size:18px;margin:0 0 24px}
.links a{display:inline-block;margin:4px 16px 4px 0}
.draft{background:#FFF1C9;color:#5A4500;border-radius:12px;padding:10px 14px;font-size:14px;margin-bottom:16px}
footer{max-width:720px;margin:0 auto;padding:0 16px 40px;color:var(--faint);font-size:13px}
"""


def page(title: str, body: str, *, description: str, draft: bool) -> str:
    robots = '<meta name="robots" content="noindex">' if draft else ""
    banner = ('<p class="draft">Draft — not yet published. Fields in brackets are still to be filled.</p>'
              if draft else "")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
{robots}
<style>{CSS}</style>
</head>
<body>
<header class="site"><a class="brand" href="/">502 Design Studio</a>
<nav><a href="/meridiem/">Meridiem</a><a href="/meridiem/support/">Support</a><a href="/meridiem/privacy/">Privacy</a></nav>
</header>
<main>
{banner}
{body}
</main>
<footer>© 2025–2026 502 Design Studio · <a href="mailto:info@502ds.dev">info@502ds.dev</a></footer>
</body>
</html>
"""


HOME = """
<h1>502 Design Studio</h1>
<p class="lede">Apps for the night and the morning: sleep, breathing and therapy, read against your own history.</p>
<div class="card">
<h2><a href="/meridiem/">Meridiem</a></h2>
<p>Days and nights. A quiet wake. — For iPhone and Apple Watch.</p>
<p class="links"><a href="/meridiem/support/">Support</a><a href="/meridiem/privacy/">Privacy Policy</a>
<a href="/meridiem/terms/">Terms of Use</a></p>
</div>
<p>Contact: <a href="mailto:info@502ds.dev">info@502ds.dev</a></p>
"""

MERIDIEM = """
<h1>Meridiem</h1>
<p class="lede">Days and nights. A quiet wake.</p>
<p>Meridiem reads the sleep and heart data your Apple Watch already records, and turns it into something you can act
on — measured against your own nights, not against other people.</p>
<ul>
<li><strong>Today</strong> — one score for your nights, and the four signals of the night against your usual.</li>
<li><strong>Sleep</strong> — one night in detail, scored in five parts against your own history.</li>
<li><strong>Alar-ME</strong> — an alarm that starts quiet, rises slowly and stops once you walk; or a silent tap on
your wrist.</li>
<li><strong>Breathe</strong> — guided breathing toward six breaths a minute, with your heart measured on the watch.</li>
<li><strong>Recovery</strong> and <strong>Move</strong> — heart rate variability and steps, against your usual.</li>
</ul>
<p><strong>Private by design.</strong> No account and no analytics. Nothing leaves your devices unless you connect a
service yourself.</p>
<p>Meridiem is for general wellness. It does not diagnose, treat or prevent any condition.</p>
<p class="links"><a href="/meridiem/support/">Support</a><a href="/meridiem/privacy/">Privacy Policy</a>
<a href="/meridiem/terms/">Terms of Use</a></p>
"""


def write(path: str, content: str) -> None:
    target = OUT / path / "index.html" if path else OUT / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main() -> int:
    draft = "--draft" in sys.argv
    data = publishing_data()
    missing: dict[str, list[str]] = {}
    built: dict[str, str] = {}
    for path, src in PAGES.items():
        md = public_text(src.read_text(encoding="utf-8"))
        for field, value in data.items():
            md = md.replace(field, value)
        left = gaps(md)
        if left:
            missing[path] = left
        built[path] = md

    if missing:
        print(("· built as drafts" if draft else "· left out until filled") + " — fields still empty:")
        for path, left in missing.items():
            print(f"  /{path}: {', '.join(left)}")
        print(f"  fill them in {DATA}")

    import shutil
    shutil.rmtree(OUT, ignore_errors=True)   # a page left out must not survive from an earlier build
    for path, md in built.items():
        if path in missing and not draft:
            continue
        body = markdown.markdown(md, extensions=["tables"])
        title = re.search(r"^#\s+(.+)$", md, flags=re.M)
        name = title.group(1).strip() if title else path
        write(path, page(name, body, description=f"{name} — 502 Design Studio", draft=draft and path in missing))
    write("", page("502 Design Studio", HOME, description="Apps for the night and the morning.", draft=False))
    write("meridiem", page("Meridiem", MERIDIEM, description="Meridiem — Days and nights. A quiet wake.", draft=False))
    (OUT / "404.html").write_text(page("Not found", '<h1>Not found</h1><p><a href="/">502ds.dev</a></p>',
                                       description="Not found", draft=False), encoding="utf-8")
    (OUT / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    count = len(PAGES) + 2 - (0 if draft else len(missing))
    state = ("draft" if draft else "for publishing") + (f" · {len(missing)} page(s) waiting on a field" if missing else "")
    print(f"✓ built {count} pages in {OUT} · {state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
