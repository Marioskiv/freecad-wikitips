"""Build WikiTips data from the up-to-date offline FreeCAD wiki
(github.com/Reqrefusion/FreeCAD-Documentation-html).

usage: extract_html.py <repo>/wiki out.json
Writes out.json and out.json.images.txt (image file names under wiki/File).
"""
import json
import os
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

WIKI, OUT = sys.argv[1], sys.argv[2]
KEEP_TAGS = {"b", "strong", "i", "em", "code", "sub", "sup"}
DESC_LIMIT = 420


def inline_html(node):
    """Return simplified inline HTML: keep b/i/code, drop links/images/spans."""
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            out.append(str(c).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        elif isinstance(c, Tag):
            if c.name in ("img", "figure", "style", "script", "sup") and c.name != "sup":
                continue
            if c.name in ("ul", "ol", "table", "div"):
                continue  # nested blocks handled elsewhere
            cls = " ".join(c.get("class", []))
            if "ButtonTemplate" in cls:
                out.append("<b>%s</b>" % inline_html(c).strip())
                continue
            if c.name == "small" or "versionadded" in cls:
                inner = inline_html(c).strip()
                out.append(inner)
                continue
            inner = inline_html(c)
            if c.name in ("strong",):
                out.append("<b>%s</b>" % inner)
            elif c.name in ("em",):
                out.append("<i>%s</i>" % inner)
            elif c.name in KEEP_TAGS:
                out.append("<%s>%s</%s>" % (c.name, inner, c.name))
            else:
                out.append(inner)
    s = "".join(out)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"<(b|i|code)>\s*</\1>", "", s)
    s = re.sub(r",?\s*\(?see (the )?(<[^>]+>)?(\w+ ){0,2}(\w+)(</[^>]+>)? (below|above)\)?", "", s, flags=re.I)
    s = re.sub(r"\(?\s*introduced in (?:version )?(\d[\d.]*)\s*\)?\s*:?", r"(v\1) ", s, flags=re.I)
    s = re.sub(r"\s+([.,;:)])", r"\1", s)
    s = re.sub(r"\(\s+", "(", s)
    return s.strip()


def section_nodes(soup, sec_id):
    span = soup.find("span", {"class": "mw-headline", "id": sec_id})
    if span is None:
        return []
    h = span.find_parent(re.compile("^h[1-6]$"))
    nodes = []
    for sib in h.next_siblings:
        if isinstance(sib, Tag) and re.match("^h[12]$", sib.name):
            break
        if isinstance(sib, Tag):
            nodes.append(sib)
    return nodes


def is_caption(p):
    st = (p.get("style") or "").replace(" ", "")
    return "font-style:italic" in st


def pick_image(nodes, icon_name):
    for n in nodes:
        imgs = [n] if n.name == "img" else n.find_all("img")
        for img in imgs:
            src = img.get("src", "")
            if not src.startswith("File/"):
                continue
            try:
                w = int(img.get("width") or 0)
            except ValueError:
                w = 0
            if 0 < w < 100:
                continue
            base = src[5:]
            if base.lower() == icon_name.lower():
                continue
            if re.search(r"(^Arrow-|^Workbench_|Information|Warning|Fc_|Edit-)", base):
                continue
            return base
    return None


def describe(nodes):
    parts, total = [], 0
    for n in nodes:
        if n.name == "p" and not is_caption(n):
            t = inline_html(n)
            if t and len(re.sub("<[^>]+>", "", t)) > 2:
                parts.append("<p>%s</p>" % t)
                total += len(t)
        elif n.name in ("ul", "ol"):
            items = [inline_html(li) for li in n.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if items:
                parts.append("<ul>%s</ul>" % "".join("<li>%s</li>" % i for i in items[:6]))
                total += sum(len(i) for i in items[:6])
        if total > DESC_LIMIT:
            break
    return "".join(parts)


SKIP_STEP = re.compile(r"(several ways to invoke|ways to invoke the|^press the .{0,80} (button|icon)|"
                       r"^select the .{0,120} option from the menu\.?$|^use the keyboard shortcut)", re.I)


def usage(nodes, maxn=6):
    for n in nodes:
        if n.name == "ol":
            steps = []
            for li in n.find_all("li", recursive=False):
                t = inline_html(li)
                plain = re.sub("<[^>]+>", "", t)
                if not t or SKIP_STEP.search(plain) or len(re.sub(r"\W", "", plain)) < 6:
                    continue
                if len(plain) > 230:
                    t = re.sub("<[^>]+>", "", t)[:227].rsplit(" ", 1)[0] + "…"
                steps.append(t)
                if len(steps) >= maxn:
                    break
            return steps
    return []


def infobox(soup):
    box = soup.find("table", class_="fcinfobox")
    if box is None:
        return None
    info = {}
    title = box.find("td", class_="ctTitle")
    info["title"] = title.get_text(" ", strip=True) if title else ""
    for th in box.find_all("th"):
        key = th.get_text(" ", strip=True)
        td = th.find_parent("tr").find_next_sibling("tr")
        if td is None:
            continue
        val = td.get_text(" ", strip=True)
        info[key] = val
    return info


data, images = {}, set()
names = sorted(f for f in os.listdir(WIKI) if f.endswith(".html") and "_" in f
               and not f.startswith(("Template;", "Category;", "Macro_", "Talk;", "User;")))
for fn in names:
    path = os.path.join(WIKI, fn)
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    if "fcinfobox" not in html or "Menu location" not in html:
        continue
    soup = BeautifulSoup(html, "lxml")
    info = infobox(soup)
    if not info or "Menu location" not in info:
        continue
    name = fn[:-5]
    desc_nodes = section_nodes(soup, "Description")
    use_nodes = section_nodes(soup, "Usage")
    d = describe(desc_nodes)
    img = pick_image(desc_nodes, name + ".svg") or pick_image(use_nodes, name + ".svg")
    if not img:  # any other picture of the page (options, examples, task panel)
        body = soup.find("table", class_="fcinfobox")
        rest = [n for n in body.find_all_next(["figure", "img"])] if body else []
        rest = [n for n in rest if not n.find_parent(class_=re.compile("docnav|navbox|NavFrame|fcinfobox"))]
        img = pick_image(rest, name + ".svg")
    if not d and not img:
        continue
    e = {"t": info.get("title") or name.replace("_", " "), "d": d, "u": usage(use_nodes)}
    menu = info.get("Menu location", "").replace("→", "→")
    if menu and menu.lower() not in ("none", "-"):
        e["m"] = re.sub(r"\s*→\s*", " → ", menu)
    sc = info.get("Default shortcut", "")
    if sc and sc.lower() not in ("none", "-"):
        e["k"] = sc
    ver = info.get("Introduced in version", "")
    if ver and ver != "-":
        e["v"] = ver
    if img:
        e["i"] = img
        images.add(img)
    data[name] = e

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
with open(OUT + ".images.txt", "w") as f:
    f.write("\n".join(sorted(images)))
print(len(data), "commands,", len(images), "images")
