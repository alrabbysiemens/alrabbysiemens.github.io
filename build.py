#!/usr/bin/env python3
"""Builds alrabbysiemens.github.io from the files in content/.

    python build.py            # normal build into _site/ (for GitHub Pages)
    python build.py --preview  # links point at index.html files (for local preview)

You never need to edit this file to update the site: change the files in content/.
"""
import json, os, re, shutil, sys, datetime
from pathlib import Path

import yaml, markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
PREVIEW = "--preview" in sys.argv

def load(name, default=None):
    p = ROOT / "content" / name
    if not p.exists():
        return default
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return default if data is None else data

profile = load("profile.yml", {})
experience = load("experience.yml", [])
education = load("education.yml", [])
language = load("languages.yml", [])
training = load("training.yml", [])
skills = load("skills.yml", [])
awards = load("awards.yml", [])
pubs = load("publications.yml", [])
projects = load("projects.yml", [])
news = load("news.yml", [])
beyond = load("beyond.yml", {})
media = load("media.yml", {}) or {}

# ---------- experience (LinkedIn style) ----------
TODAY = datetime.date.today()
def _ym(s):
    s = str(s or "").strip()
    if not s or s.lower() == "present":
        return (TODAY.year, TODAY.month), s.lower() == "present"
    d = datetime.datetime.strptime(s, "%b %Y")
    return (d.year, d.month), False
def _dur(a, b):
    m = (b[0] - a[0]) * 12 + (b[1] - a[1]) + 1
    y, mo = divmod(max(m, 1), 12)
    parts = ([f"{y} yr{'s' if y > 1 else ''}"] if y else []) + ([f"{mo} mo{'s' if mo > 1 else ''}"] if mo else [])
    return " ".join(parts)
for o in experience:
    for r in o.get("roles", []):
        r["_s"], _ = _ym(r["start"])
        r["_e"], r["current"] = _ym(r.get("end") or r["start"])
        r["duration"] = _dur(r["_s"], r["_e"])
    o["roles"].sort(key=lambda r: (r["current"], r["_e"], r["_s"]), reverse=True)
    o["current"] = any(r["current"] for r in o["roles"])
    o["_s"] = min(r["_s"] for r in o["roles"]); o["_e"] = max(r["_e"] for r in o["roles"])
    o["latest_start"] = max(r["_s"] for r in o["roles"])
    o["duration"] = _dur(o["_s"], o["_e"])
    words = [w for w in re.findall(r"[A-Za-z0-9]+", o.get("short") or o["org"])]
    o["initials"] = (o.get("short") or "".join(w[0] for w in words))[:6].upper()
experience.sort(key=lambda o: (o["current"], o["latest_start"] if o["current"] else o["_e"]), reverse=True)

# ---------- map projection (matches templates/bd.json) ----------
BD = json.loads((ROOT / "templates" / "bd.json").read_text())

def project_xy(lat, lon):
    return round((float(lon) - BD["lon0"]) * BD["kx"], 1), round((BD["lat0"] - float(lat)) * BD["ky"], 1)

n = 0
for p in projects:
    if str(p.get("lat", "")).strip() and str(p.get("lon", "")).strip():
        n += 1
        p["num"] = n
        p["x"], p["y"] = project_xy(p["lat"], p["lon"])
    else:
        p["num"] = None
    p["slug"] = re.sub(r"[^a-z0-9]+", "-", (p.get("short") or p.get("title") or (p.get("org", "") + " " + p.get("role", ""))).lower()).strip("-")[:80]

def _pt(d):
    d = dict(d)
    d["x"], d["y"] = project_xy(d["lat"], d["lon"])
    return d

DISTRICTS = json.loads((ROOT / "templates" / "districts.json").read_text())
DISPLAY = {"Nawabganj": "Chapai Nawabganj", "Sirajgonj": "Sirajganj"}
ALIAS = {"chapainawabganj": "Nawabganj", "chapai": "Nawabganj", "nawabganj": "Nawabganj", "chittagong": "Chattogram",
         "comilla": "Cumilla", "barisal": "Barishal", "jessore": "Jashore", "bogra": "Bogura", "sirajganj": "Sirajgonj",
         "moulvibazar": "Maulvibazar", "jhalakathi": "Jhalokati", "jhalakati": "Jhalokati", "khagrachhari": "Khagrachari",
         "netrakona": "Netrokona", "coxsbazar": "Cox's Bazar", "coxbazar": "Cox's Bazar"}
_key = lambda s: re.sub(r"[^a-z]", "", str(s).lower())
_by_key = {_key(d["name"]): d["name"] for d in DISTRICTS}
def district_name(s):
    k = _key(s)
    return _by_key.get(k) or ALIAS.get(k)
visited = set()
for v in beyond.get("visited_districts") or []:
    n = district_name(v)
    if n: visited.add(n)
    else: print(f"WARNING: unknown district in beyond.yml: {v}")
home_d = district_name((beyond.get("hometown") or {}).get("name", ""))
if home_d: visited.add(home_d)
cur_d = district_name(beyond.get("current_home", "") or "")
anc_d = district_name(beyond.get("ancestral_home", "") or "")
for x in (cur_d, anc_d):
    if x: visited.add(x)
district_map = [dict(d, label=DISPLAY.get(d["name"], d["name"]), visited=d["name"] in visited, home=d["name"] == home_d,
                     current=d["name"] == cur_d, ancestral=d["name"] == anc_d) for d in DISTRICTS]
RIVERS = json.loads((ROOT / "templates" / "rivers.json").read_text())
RIVER_LABELS = [{"name": n, "x": round((lo - BD["lon0"]) * BD["kx"], 1), "y": round((BD["lat0"] - la) * BD["ky"], 1), "rot": r}
                for n, la, lo, r in [("Teesta", 26.12, 89.22, 40), ("Jamuna", 24.6, 89.83, 86), ("Padma", 24.1, 88.86, 22),
                                     ("Meghna", 22.85, 90.84, 74), ("Old Brahmaputra", 24.72, 90.18, 46), ("Surma", 25.13, 91.55, 0),
                                     ("Kushiyara", 24.55, 91.78, 18), ("Brahmaputra", 25.55, 89.82, 80)]]
beyond["districts"] = district_map
beyond["visited_list"] = sorted(DISPLAY.get(n, n) for n in visited)

ht = beyond.get("hometown")
if ht:
    beyond["hometown"] = _pt(ht)
beyond["places"] = [_pt(p) for p in (beyond.get("places") or [])]

# ---------- publications ----------
CATS = [("book", "Books"), ("chapter", "Book Chapters"), ("journal", "Journal Articles"),
        ("proceeding", "Conference Proceedings"), ("oped", "Op-eds")]
STATUS = {"published": "Published", "under-review": "Under review", "in-progress": "In progress", "accepted": "Accepted"}

def bold_me(authors):
    s = str(escape(authors or ""))
    return Markup(re.sub(r"(Siemens,\s*A\.?\s*R\.?)", r"<strong>\1</strong>", s))

for p in pubs:
    p["authors_html"] = bold_me(p.get("authors"))
    p["status_label"] = STATUS.get(p.get("status", "published"), p.get("status", ""))
    doi = str(p.get("doi") or "").strip()
    p["doi"] = doi
    p["doi_url"] = ("https://doi.org/" + doi) if doi else ""
pub_groups = [{"key": k, "label": l, "pubs": sorted([p for p in pubs if p.get("category") == k],
              key=lambda x: str(x.get("year") or "9999"), reverse=True)} for k, l in CATS]
counts = {g["key"]: len(g["pubs"]) for g in pub_groups}

# ---------- write-ups ----------
def compact(n):
    """1234 -> 1.2k, 11050 -> 11.1k; below 100 shows nothing."""
    if n < 100:
        return ""
    if n < 1000:
        return str(n)
    v = round(n / 1000, 1)
    return (f"{v:.1f}".rstrip("0").rstrip(".")) + "k"

def parse_md(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    meta["html"] = Markup(markdown.markdown(body, extensions=["extra"]))
    meta["slug"] = path.stem
    d = meta.get("date")
    if isinstance(d, (datetime.date, datetime.datetime)):
        meta["date_str"] = d.strftime("%d %b %Y")
        meta["sort"] = d.isoformat()
    else:
        meta["date_str"] = str(d or "")
        meta["sort"] = str(d or "")
    lang = str(meta.get("lang", "en")).lower()
    meta["lang"] = "bn" if lang in ("bn", "bangla", "bengali", "বাংলা") else "en"
    words = len(re.sub(r"<[^>]+>", " ", str(meta["html"])).split())
    meta["minutes"] = max(1, round(words / 200))
    meta["reads"] = int(meta.get("reads") or 0)
    meta["reads_str"] = compact(meta["reads"])
    return meta

writeups = sorted([parse_md(p) for p in (ROOT / "content" / "writeups").glob("*.md")],
                  key=lambda m: m["sort"], reverse=True)

# ---------- media ----------
YT = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{11})")
for v in media.get("videos") or []:
    m = YT.search(v.get("url", ""))
    v["youtube_id"] = m.group(1) if m else ""

def asset(path):
    return str(path or "").lstrip("/")

# ---------- render ----------
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html", "xml"]))

def month(s):
    s = str(s)
    try:
        return datetime.datetime.strptime(s, "%Y-%m").strftime("%b %Y")
    except ValueError:
        return s

env.filters["month"] = month
env.filters["asset"] = asset
env.filters["md"] = lambda t: Markup(markdown.markdown(t or "", extensions=["extra"]))
ICONS = json.loads((ROOT / "templates" / "icons.json").read_text())

def icon(label, size=18, mono=False):
    i = ICONS.get(label)
    if not i:
        return ""
    fill = "currentColor" if mono else "#" + i["hex"]
    return Markup(f'<svg class="pi" aria-hidden="true" width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}"><path d="{i["path"]}"/></svg>')

env.globals["icon"] = icon
env.filters["year"] = lambda d: (re.search(r"(19|20)\d\d", str(d or "")) or [""])[0]

NAV = [
    {"label": "Home", "href": "", "key": "home"},
    {"label": "About", "key": "about", "children": [
        {"label": "Education", "href": "about/education/"}, {"label": "Experience", "href": "about/"},
        {"label": "Training", "href": "about/training/"}, {"label": "Skills", "href": "about/skills/"}, {"label": "Leadership", "href": "about/leadership/"},
        {"label": "Awards & Achievements", "href": "about/awards/"}, {"label": "Beyond Work", "href": "about/beyond-work/"}]},
    {"label": "Research", "key": "research", "children": [
        {"label": "Projects", "href": "research/"}, {"label": "Publications", "href": "publications/"}, {"label": "SIEM Lab", "href": "research/siem-lab/"}]},
    {"label": "Writing", "href": "writing/", "key": "writing"},
    {"label": "Media", "key": "media", "children": [
        {"label": "In the News", "href": "media/news/"}, {"label": "Gallery", "href": "media/gallery/"}, {"label": "Videos", "href": "media/videos/"},
        {"label": "Your Presence", "href": "media/your-presence/"}]},
    {"label": "Contact", "href": "contact/", "key": "contact"},
]
ABOUT_TABS = NAV[1]["children"]

pages_written = []

def render(template, out_path, **ctx):
    depth = out_path.count("/")
    base = "../" * depth
    def url(href):
        href = href or ""
        if href.startswith("http") or href.startswith("mailto:") or href.startswith("#"):
            return href
        if PREVIEW and (href == "" or href.endswith("/")):
            href = href + "index.html"
        return base + href
    html = env.get_template(template).render(
        p=profile, nav=NAV, about_tabs=ABOUT_TABS, url=url, base=base, counts=counts,
        path=out_path.replace("index.html", ""), year=datetime.date.today().year, bd=BD, rivers=RIVERS, river_labels=RIVER_LABELS, **ctx)
    dest = OUT / out_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    pages_written.append(out_path.replace("index.html", ""))

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    latest_journal = [p for p in pubs if p.get("category") == "journal" and p.get("status") == "published"]
    render("home.html", "index.html", section="home", districts=district_map, beyond=beyond, news=news[:3], projects=[x for x in projects if x.get("group") == "research"],
           selected=latest_journal[:3], writeups=writeups[:2])
    render("about_experience.html", "about/index.html", section="about", tab="about/", experience=experience,
           title="Experience")
    render("about_education.html", "about/education/index.html", section="about", tab="about/education/",
           education=education, language=language, title="Education")
    render("about_training.html", "about/training/index.html", section="about", tab="about/training/",
           training=training, title="Training")
    render("about_skills.html", "about/skills/index.html", section="about", tab="about/skills/",
           skills=skills, language=language, title="Skills")
    render("about_awards.html", "about/awards/index.html", section="about", tab="about/awards/",
           awards=awards, title="Awards & Achievements")
    render("about_beyond.html", "about/beyond-work/index.html", section="about", tab="about/beyond-work/",
           beyond=beyond, title="Beyond Work", personal=True)
    render("about_leadership.html", "about/leadership/index.html", section="about", tab="about/leadership/",
           beyond=beyond, title="Leadership")
    render("lab.html", "research/siem-lab/index.html", section="research", lab=yaml.safe_load(open(ROOT / "content" / "lab.yml", encoding="utf-8")), title="SIEM Lab")
    render("research.html", "research/index.html", section="research", districts=district_map, projects=projects, title="Projects")
    render("publications.html", "publications/index.html", section="research", groups=pub_groups, title="Publications")
    render("writing.html", "writing/index.html", section="writing", writeups=writeups, title="Write-ups", personal=True)
    for i, w in enumerate(writeups):
        newer = writeups[i-1] if i > 0 else None
        older = writeups[i+1] if i + 1 < len(writeups) else None
        render("writeup.html", f"writing/{w['slug']}/index.html", section="writing", w=w, newer=newer, older=older, title=w.get("title", ""), personal=True)
    render("gallery.html", "media/gallery/index.html", section="media", gallery=media.get("gallery") or [],
           title="Gallery", personal=True)
    render("press.html", "media/news/index.html", section="media", press=media.get("press") or [], title="In the News")
    render("videos.html", "media/videos/index.html", section="media", videos=media.get("videos") or [], vp=media.get("video_page") or {}, title="Videos")
    notes = [n for n in (load("guestbook.yml", []) or []) if n and n.get("approved")]
    render("presence.html", "media/your-presence/index.html", section="media", notes=notes, title="Your Presence", personal=True)
    render("contact.html", "contact/index.html", section="contact", title="Contact")
    render("404.html", "404.html", section="", title="Page not found")
    # sitemap + robots
    site = profile.get("site_url", "").rstrip("/")
    today = datetime.date.today().isoformat()
    urls = "".join(f"<url><loc>{site}/{u}</loc><lastmod>{today}</lastmod></url>"
                   for u in pages_written if u != "404.html")
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    for g in (OUT / "img").rglob(".gitkeep"):
        g.unlink()
    for g in OUT.rglob(".gitkeep"):
        g.unlink()
    print(f"Built {len(pages_written)} pages into {OUT}")

if __name__ == "__main__":
    build()
