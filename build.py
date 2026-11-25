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
    "syncthesis/terms": REPOS / "syncThesis/docs/legal/terms-of-use.md",
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
        # The label's own colon, the first after it: a value may hold colons too (https://…).
        m = re.search(re.escape(label) + r"[^\n:]*(?:\n[ \t]+[^\n:]*)*:[ \t]*([^\n]*)", text)
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


# **The site's look** (`Meridiem` M-109): the landing page's language for every page — Rubik, Day as the ground with a
# switch to Night (the same choice the landing keeps, `meridiem.ground`), soft glows on the ground and surfaces with
# depth. A legal page is one lit card of text on that ground.
CSS = """
:root{--bg:#F4FCFE;--card:#FFFFFF;--ink:#1A1A2E;--muted:#5F5F71;--faint:#71718A;--soft:#E1F6F8;--line:#D5ECEF;
--accent:#12B5C2;--accent-ink:#0A7E8A;--blue:#286193;--turq:#3E9487;--sun:#F6A531;--glow:rgba(18,181,194,.28);
--ground:radial-gradient(1000px 560px at 88% -6%,rgba(18,181,194,.10),transparent 62%),
radial-gradient(800px 500px at 8% 4%,rgba(246,165,49,.09),transparent 60%),
radial-gradient(900px 600px at 50% 105%,rgba(40,97,147,.06),transparent 60%);
--surface:var(--card);--lift:0 1px 2px rgba(26,26,46,.05),0 12px 28px -18px rgba(10,60,80,.28);
--press:0 6px 16px -8px rgba(18,181,194,.55);color-scheme:light}
body[data-ground="night"]{--bg:#0C3242;--card:#11313C;--ink:#DCEEF1;--muted:#8FB6BE;--faint:#799BA3;--soft:#1B4450;
--line:#1F4A56;--accent:#5BD3DE;--accent-ink:#5BD3DE;--blue:#598BBA;--turq:#59B4A6;--glow:rgba(91,211,222,.25);
--ground:radial-gradient(1100px 620px at 85% -8%,rgba(91,211,222,.16),transparent 62%),
radial-gradient(900px 560px at -5% 38%,rgba(89,139,186,.20),transparent 60%),
radial-gradient(800px 500px at 60% 100%,rgba(246,165,49,.07),transparent 60%),
linear-gradient(180deg,#0E3747 0%,#0A2834 55%,#071E28 100%);
--surface:linear-gradient(180deg,#15404D 0%,#0F2F3A 100%);
--lift:0 1px 0 rgba(255,255,255,.06) inset,0 18px 40px -20px rgba(0,0,0,.65);
--press:0 8px 22px -8px rgba(91,211,222,.55);color-scheme:dark}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);background-image:var(--ground);background-attachment:fixed;color:var(--ink);
font:400 16px/1.65 "Rubik",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;transition:background .6s,color .6s;
font-variant-numeric:tabular-nums}
a{color:var(--accent-ink)}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:8px}
.wrap{max-width:1080px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));
padding-right:max(16px,env(safe-area-inset-right,0px))}
.bar{position:sticky;top:0;z-index:9;background:color-mix(in srgb,var(--bg) 82%,transparent);
backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.bar .wrap{display:flex;align-items:center;gap:20px;padding-block:12px}
.brand{font:600 18px "Rubik",system-ui,sans-serif;color:var(--ink);text-decoration:none;display:flex;align-items:center;gap:8px}
.brand i{width:10px;height:10px;border-radius:50%;background:var(--sun);box-shadow:0 0 12px var(--sun)}
.bar nav{display:flex;gap:18px;margin-left:auto;font-size:15px}
.bar nav a{color:var(--muted);text-decoration:none}
.bar nav a:hover{color:var(--ink)}
.ground{display:flex;border:1px solid var(--line);border-radius:999px;padding:3px;background:var(--surface);box-shadow:var(--lift)}
.ground button{font:500 13px "Rubik",system-ui,sans-serif;border:0;background:none;color:var(--muted);padding:5px 11px;
border-radius:999px;cursor:pointer}
.ground button[aria-pressed="true"]{background:var(--accent);color:var(--card);box-shadow:var(--press)}
@media (max-width:640px){.bar nav{display:none}.ground{margin-left:auto}}
main{padding-block:32px 56px}
.doc{max-width:780px;margin:0 auto;background:var(--surface);border:1px solid var(--line);border-radius:24px;
box-shadow:var(--lift);padding:28px clamp(18px,4vw,40px)}
h1,h2,h3{font-family:"Rubik",system-ui,sans-serif;text-wrap:balance;letter-spacing:-.01em}
h1{font-size:clamp(30px,4.6vw,40px);line-height:1.12;margin:4px 0 12px;font-weight:600}
h2{font-size:21px;margin:34px 0 8px;font-weight:600}
h3{font-size:17px;margin:24px 0 6px;font-weight:600}
p,li{color:var(--ink)}
strong{font-weight:600}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:15px;display:block;overflow-x:auto}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600}
blockquote{margin:16px 0;padding:12px 16px;background:var(--soft);border-radius:14px}
.draft{background:#FFF1C9;color:#5A4500;border-radius:12px;padding:10px 14px;font-size:14px;margin-bottom:16px}
.lede{color:var(--muted);font-size:19px;max-width:34em;margin:0}
.eyebrow{font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--accent-ink);margin:0}
.hero{display:grid;gap:14px;padding-block:24px 36px}
.apps{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}
.app{background:var(--surface);border:1px solid var(--line);border-radius:24px;box-shadow:var(--lift);padding:24px;
display:flex;flex-direction:column;gap:12px;min-width:0}
.app.main{border:2px solid var(--accent);box-shadow:var(--lift),0 0 40px -14px var(--glow)}
.app h2{margin:0}
.app h2 a{color:var(--ink);text-decoration:none}
.app img{width:120px;height:120px;object-fit:contain;align-self:flex-start}
.app p{margin:0;color:var(--muted)}
.links{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:auto}
.go{display:inline-flex;align-self:flex-start;background:var(--accent);color:var(--card);text-decoration:none;font-weight:600;
border-radius:12px;padding:9px 16px;box-shadow:var(--press)}
@media (max-width:760px){.apps{grid-template-columns:1fr}}
footer .wrap{padding-block:24px 40px;border-top:1px solid var(--line);color:var(--faint);font-size:14px;display:flex;
flex-wrap:wrap;gap:10px 22px}
footer a{color:var(--muted)}
"""

# The Day/Night switch, the same as the landing page's.
GROUND_JS = """<script>
(() => {
  const set = (g) => {
    document.body.dataset.ground = g;
    document.getElementById("g-day").setAttribute("aria-pressed", String(g === "day"));
    document.getElementById("g-night").setAttribute("aria-pressed", String(g === "night"));
    try { localStorage.setItem("meridiem.ground", g); } catch (e) {}
  };
  document.getElementById("g-day").addEventListener("click", () => set("day"));
  document.getElementById("g-night").addEventListener("click", () => set("night"));
  try { if (localStorage.getItem("meridiem.ground") === "night") set("night"); } catch (e) {}
})();
</script>"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600&display=swap">')


def page(title: str, body: str, *, description: str, draft: bool, doc: bool = True) -> str:
    """A page of the site. `doc` sets its body in one lit card of text (the legal and support pages); the home page
    lays out its own."""
    robots = '<meta name="robots" content="noindex">' if draft else ""
    banner = ('<p class="draft">Draft — not yet published. Fields in brackets are still to be filled.</p>'
              if draft else "")
    inner = f'<article class="doc">{banner}{body}</article>' if doc else banner + body
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
{robots}
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="bar"><div class="wrap">
<a class="brand" href="/"><i aria-hidden="true"></i>502 Design Studio</a>
<nav aria-label="Site"><a href="/meridiem/">Meridiem</a><a href="/meridiem/support/">Support</a><a href="/meridiem/privacy/">Privacy</a></nav>
<div class="ground" role="group" aria-label="Page ground"><button id="g-day" type="button" aria-pressed="true">Day</button><button id="g-night" type="button" aria-pressed="false">Night</button></div>
</div></header>
<main><div class="wrap">
{inner}
</div></main>
<footer><div class="wrap"><span>© 2025–2026 502 Design Studio</span><span>info@502ds.dev</span></div></footer>
{GROUND_JS}
</body>
</html>
"""


HOME = """
<section class="hero">
<p class="eyebrow">502 Design Studio</p>
<h1>Apps for the night and the morning.</h1>
<p class="lede">Sleep, breathing and therapy, read against your own history.</p>
</section>
<div class="apps">
<article class="app main">
<img src="/meridiem/img/wordmark.png" alt="The Meridiem mark">
<h2><a href="/meridiem/">Meridiem</a></h2>
<p>Days and nights. A quiet wake. Your sleep, heart and PAP therapy, read against your own nights, and an alarm that
wakes you, not the room. For iPhone and Apple Watch.</p>
<a class="go" href="/meridiem/">See Meridiem</a>
<p class="links"><a href="/meridiem/support/">Support</a><a href="/meridiem/privacy/">Privacy Policy</a><a href="/meridiem/terms/">Terms of Use</a></p>
</article>
<article class="app">
<h2>syncThesis.IO</h2>
<p>Breathing therapy and sleep studies, read together with the clinicians who follow them. By invitation.</p>
<p class="links"><a href="/syncthesis/privacy/">Privacy Policy</a><a href="/syncthesis/terms/">Terms of Use</a></p>
</article>
</div>
"""

# **Meridiem's landing page** (`Meridiem` M-109 Inc 3): written as one page of its own (`landing/meridiem.html`, the
# page's head and body without the document's shell) with its images beside it (`landing/img/`), and wrapped here.
LANDING = ROOT / "landing"


def landing(name: str) -> str:
    """The landing page as a whole document: what comes before its closing </style> is the head, the rest the body."""
    src = (LANDING / f"{name}.html").read_text(encoding="utf-8")
    src = re.sub(r'<meta name="claude:[^"]*"[^>]*>\n?', "", src)   # the preview's own hint, not the site's
    cut = src.index("</style>") + len("</style>")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{src[:cut]}
</head>
<body>
{src[cut:].strip()}
</body>
</html>
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
            # A web address goes in as a link, not as text to copy.
            md = md.replace(field, f"<{value}>" if value.startswith("http") else value)
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
        # A document's header lines (**Last updated:** …, **App:** …) each on its own line: markdown joins lines.
        md = re.sub(r"^(\*\*[^\n]+)\n(?=\*\*)", r"\1  \n", md, flags=re.M)
        body = markdown.markdown(md, extensions=["tables"])
        title = re.search(r"^#\s+(.+)$", md, flags=re.M)
        name = title.group(1).strip() if title else path
        write(path, page(name, body, description=f"{name} — 502 Design Studio", draft=draft and path in missing))
    write("", page("502 Design Studio", HOME, description="Apps for the night and the morning.", draft=False, doc=False))
    write("meridiem", landing("meridiem"))
    shutil.copytree(LANDING / "img", OUT / "meridiem" / "img")
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
